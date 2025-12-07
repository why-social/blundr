from pathlib import Path
from data.prediction import predictions_to_csv
from fastapi import FastAPI, UploadFile, File, Form 
from model.model import Model

app = FastAPI()
model = Model(Path("/etc/model.pth"))

@app.post("/infer")
async def get_audio(
    session_id: str = Form(...), 
    user_id: str = Form(...), 
    audio: UploadFile = File(...),
    transcript: str = Form(...),
):
    audio_path = Path(f"/tmp/Sesh_id:{session_id}user_id:{user_id}.wav")

    # TODO: avoid writing to disk and operate in-memory?
    with open(audio_path, "wb") as file:
        file.write(await audio.read())

    output = model.infer(audio_path, transcript)

    return {
        "status": 200,
        "session_id": session_id,
        "user_id": user_id,
        "predictions": predictions_to_csv(output),
    }

