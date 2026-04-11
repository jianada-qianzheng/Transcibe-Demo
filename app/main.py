import os
import shutil

from fastapi import FastAPI, UploadFile, File

app = FastAPI(title="transformer-api", description="A simple API for transformer models", version="1.0.0")

@app.post("/upload-audio/")
async def upload_audio_file(audio_file: UploadFile = File(...)):
    try:
        print(f"Received file: {audio_file.filename}")

       
        transcription = transcribe_audio()


        return {"transcription": transcription}
    except Exception as e:
        print(f"Error processing file: {e}")
        return {"error": "Failed to process the audio file."}

def transcribe_audio() -> str:
    
    return "transcribed text"