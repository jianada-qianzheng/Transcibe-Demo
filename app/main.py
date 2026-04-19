import os
import shutil
import tempfile
import torch

from fastapi import FastAPI, UploadFile, File
import whisper
from pyannote.audio import Pipeline

app = FastAPI(
    title="transformer-api", 
    description="A simple API for transformer models with speaker diarization", 
    version="1.0.0"
)

# 1. Load Whisper Model
print("Loading Whisper model...")
model = whisper.load_model("base")

# 2. Load Pyannote Diarization Pipeline
# You must set the HF_TOKEN environment variable before running this application.
HF_TOKEN = os.getenv("HF_TOKEN")
diarization_pipeline = None

if HF_TOKEN:
    try:
        print("Loading Pyannote Diarization Pipeline...")
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", 
            use_auth_token=HF_TOKEN
        )
        # Move pipeline to GPU if available to speed up processing
        if torch.cuda.is_available():
            diarization_pipeline.to(torch.device("cuda"))
    except Exception as e:
        print(f"Failed to load Pyannote Pipeline: {e}")
else:
    print("WARNING: HF_TOKEN environment variable is not set. Speaker diarization is disabled.")


@app.post("/upload-audio/")
async def upload_audio_file(audio_file: UploadFile = File(...)):
    try:
        print(f"Received file: {audio_file.filename}")
        
        # Process the uploaded audio file
        transcription = await transcribe_audio(audio_file)
        
        return {"transcription": transcription}
    except Exception as e:
        print(f"Error processing file: {e}")
        return {"error": "Failed to process the audio file."}


async def transcribe_audio(audio_file: UploadFile) -> dict:
    # Use NamedTemporaryFile to safely handle the uploaded audio on disk
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        try:
            content = await audio_file.read()
            temp_audio.write(content)
            temp_audio.flush() 
            print(f"Read file success: {audio_file.filename}")
            
            # Step 1: Transcribe audio using Whisper
            print("Transcribing audio...")
            whisper_result = model.transcribe(temp_audio.name)
            whisper_segments = whisper_result["segments"]
            
            # Step 2: Perform Speaker Diarization using Pyannote
            diarization_result = None
            if diarization_pipeline:
                print("Performing speaker diarization...")
                diarization_result = diarization_pipeline(temp_audio.name)
            
            # Step 3: Merge Whisper text segments with Pyannote speaker labels
            segments_with_speakers = assign_speakers(whisper_segments, diarization_result)

            return {
                "text": whisper_result["text"],
                "segments": transfer_json(segments_with_speakers)
            }
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return {"error": "Failed to process the audio file."}
            
        finally:
            # Clean up: close the file and remove the temporary file from disk
            await audio_file.close()
            if os.path.exists(temp_audio.name):
                os.remove(temp_audio.name)
    
    return {"error": "Failed to process the audio file."}


def assign_speakers(whisper_segments: list, diarization_result) -> list:
    """
    Assigns a speaker label to each Whisper transcription segment based on 
    the maximum overlapping timeframe from the Pyannote diarization result.
    """
    # If diarization failed or wasn't loaded, default all to "Unknown"
    if not diarization_result:
        for seg in whisper_segments:
            seg["speaker"] = "Unknown"
        return whisper_segments

    for seg in whisper_segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        
        max_overlap = 0.0
        assigned_speaker = "Unknown"
        
        # Iterate through all speaker turns detected by Pyannote
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            # Calculate the overlapping duration between Whisper segment and Pyannote turn
            overlap_start = max(seg_start, turn.start)
            overlap_end = min(seg_end, turn.end)
            overlap_duration = max(0.0, overlap_end - overlap_start)
            
            # Assign the speaker with the longest overlap for this specific text segment
            if overlap_duration > max_overlap:
                max_overlap = overlap_duration
                assigned_speaker = speaker
                
        seg["speaker"] = assigned_speaker
        
    return whisper_segments


def transfer_json(segments: list) -> list:
    """
    Formats the raw segments list into a clean JSON structure with proper timestamps.
    """
    try:
        json_segments = []
        for segment in segments:
            json_segments.append({
                "id": segment.get("id"),
                "speaker": segment.get("speaker", "Unknown"),
                "start": text_seconds_to_timestamp(segment.get("start")),
                "end": text_seconds_to_timestamp(segment.get("end")),
                "text": segment.get("text", "").strip()
            })
        return json_segments

    except Exception as e:
        print(f"Error converting transcription to JSON: {e}")
        return [{"error": "Failed to convert transcription to JSON."}]


def text_seconds_to_timestamp(text_seconds) -> str:
    """
    Converts raw seconds (float or string) into HH:MM:SS format.
    """
    try:
        # Whisper returns floats (e.g., 2.5). Cast to float first, then int.
        seconds = int(float(text_seconds))
    except (ValueError, TypeError):
        return "00:00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"