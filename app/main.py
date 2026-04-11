import os
import shutil

from fastapi import FastAPI, UploadFile, File
import whisper
import tempfile

app = FastAPI(title="transformer-api", description="A simple API for transformer models", version="1.0.0")

model = whisper.load_model("base")

@app.post("/upload-audio/")
async def upload_audio_file(audio_file: UploadFile = File(...)):
    try:
        print(f"Received file: {audio_file.filename}")

       
        transcription =await transcribe_audio(audio_file)


        return {"transcription": transcription}
    except Exception as e:
        print(f"Error processing file: {e}")
        return {"error": "Failed to process the audio file."}

async def transcribe_audio(audio_file: UploadFile) -> str:

    with tempfile.NamedTemporaryFile(delete=False) as temp_audio:
        try:
            content = await audio_file.read()
            temp_audio.write(content)
            temp_audio.flush() 
            print(f"read file success: {audio_file.filename}")
            
            result =  model.transcribe(temp_audio.name)

            return result
            
            
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return {"error": "Failed to process the audio file."}
            
        finally:
            await audio_file.close()
    
    return "transcribed text"