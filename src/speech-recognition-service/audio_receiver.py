from fastapi import FastAPI, UploadFile, File, Form 

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
        
    return {
        "status": "ok",
        "saved_as": file_save_path
        }
