from io import StringIO
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

    transcript = transcribe_audio()

    if r"\n" in transcript:
        transcript = transcript.replace(r"\n", "\n")  # make newlines work

    transcript = transcript.replace("\r", "")  # fix windows strings
    transcript = transcript.strip()  # sanity check blank leading/trailing lines

    df = pd.read_csv(StringIO(transcript), skipinitialspace=True)
    output = model.infer(audio_path, df)
    audio_path.unlink()  # remove the audiofile

    return {
        "session_id": session_id,
        "user_id": user_id,
        "predictions": output.to_csv(index=False),
    }
