import pandas as pd

from fastapi import FastAPI, File, Form, UploadFile
from io import StringIO
from pathlib import Path

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

    if not transcript:
        return []

    if r"\n" in transcript:
        transcript = transcript.replace(r"\n", "\n")  # make newlines work

    transcript = transcript.replace("\r", "")  # fix windows strings
    transcript = transcript.strip()  # sanity check blank leading/trailing lines

    trans_buf = StringIO(transcript)

    df = pd.read_csv(trans_buf, skipinitialspace=True)

    output = model.infer(audio_path, df)

    return {
        "session_id": session_id,
        "user_id": user_id,
        "predictions": output.to_csv(index=False),
    }
