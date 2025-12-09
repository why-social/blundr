from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, Form, UploadFile
from model.model import Model
from model.speech_recognition import transcribe_audio

app = FastAPI()
model = Model(Path("/etc/model.pth"))


@app.post("/infer")
async def infer(
    session_id: str = Form(...),
    user_id: str = Form(...),
    audio: UploadFile = File(...),
):
    audio_path = Path(f"/tmp/Sesh_id:{session_id}user_id:{user_id}.wav")

    # TODO: avoid writing to disk and operate in-memory?
    with open(audio_path, "wb") as file:
        file.write(await audio.read())

    transrcipt_df = transcribe_audio(audio_path)
    output = model.infer(audio_path, transrcipt_df)
    audio_path.unlink()  # remove the audiofile

    return {
        "session_id": session_id,
        "user_id": user_id,
        "predictions": output.to_csv(index=False),
    }
