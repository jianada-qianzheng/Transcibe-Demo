import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile
import whisper
from pyannote.audio import Pipeline

app = FastAPI()

# 1. Load Whisper model (Optimized for CPU)
whisper_model = whisper.load_model("base")

# 2. Load Pyannote Pipeline
token = os.getenv("HF_TOKEN")
print(f"DEBUG: Token loaded: {token[:8] if token else 'None'}...")

diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1", 
    token=token
)

def format_time(seconds: float) -> str:
    """Helper function to convert seconds to MM:SS or HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile):
    temp_dir = tempfile.gettempdir()
    # Unique path to avoid Windows file lock error
    temp_path = os.path.join(temp_dir, f"process_{file.filename}")
    
    try:
        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"File saved to: {temp_path}")

        # --- Task 1: Whisper Transcription ---
        print("Starting Whisper transcription...")
        transcription = whisper_model.transcribe(temp_path, fp16=False)
        
        # --- Task 2: Pyannote Diarization ---
        print("Starting Pyannote diarization...")
        raw_output = diarization_pipeline(temp_path)
        
        # Robust Annotation extraction
        annotation = None
        if hasattr(raw_output, "itertracks"):
            annotation = raw_output
        else:
            for attr in dir(raw_output):
                if not attr.startswith("_"):
                    candidate = getattr(raw_output, attr)
                    if hasattr(candidate, "itertracks"):
                        annotation = candidate
                        break
        
        if annotation is None:
            raise AttributeError("Failed to extract tracks from pyannote output.")
        
        # --- Task 3: Align Text with Speakers & Format Time ---
        whisper_segments = transcription.get("segments", [])
        combined_conversation = []
        
        for seg in whisper_segments:
            s_start = seg["start"]
            s_end = seg["end"]
            s_text = seg["text"].strip()
            
            # Use the midpoint of the whisper segment to map the speaker
            midpoint = (s_start + s_end) / 2
            current_speaker = "UNKNOWN"
            
            for turn, _, speaker in annotation.itertracks(yield_label=True):
                # If the midpoint of the spoken text falls within a speaker's turn
                if turn.start <= midpoint <= turn.end:
                    current_speaker = speaker
                    break
            
            combined_conversation.append({
                "start": format_time(s_start),
                "end": format_time(s_end),
                "speaker": current_speaker,
                "text": s_text
            })

        return {
            "status": "success",
            "filename": file.filename,
            "full_transcript": transcription["text"].strip(),
            "conversation": combined_conversation
        }

    except Exception as e:
        print(f"Process Error: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        # Release file handle and delete temp file
        file.file.close()
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_error:
                print(f"Cleanup Error: {cleanup_error}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)