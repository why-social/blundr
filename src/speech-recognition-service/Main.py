from fastapi import FastAPI, UploadFile, File, Form 
from speech_recognition import transcribe_audio

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/audio/")
async def get_audio(
    session_id: str = Form(...), 
    uuid: str = Form(...), 
    audio: UploadFile = File(...)
    ):
    
    file_save_path = f"audiofiles/Sesh_id:{session_id}user_id:{uuid}.wav"

    with open(file_save_path, "wb") as file:
        file.write(await audio.read())
        
    log = transcribe_audio()

    return {
        "status": 200,
        "log": log  
        }
