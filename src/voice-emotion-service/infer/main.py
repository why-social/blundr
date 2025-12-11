from pathlib import Path

import httpx
import shutil
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from model.model import Model
from model.speech_recognition import transcribe_audio
import os

AGGREGATOR_URL = os.environ.get("AGGREGATOR_URL", "http://localhost:42069/aggregator")

app = FastAPI()
model = Model(Path("/etc/model.pth"))
client = httpx.Client()


@app.post("/predict-audio-emotion")
async def infer(
    session_id: str = Form(...),
    user_id: str = Form(...),
    audio: UploadFile = File(...),
):
    try:
        # Save the uploaded file to a temporary location
        tmp_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix="wav") as tmp:
            shutil.copyfileobj(audio.file, tmp)
            tmp_path = Path(tmp.name)

        assert tmp_path is not None

        transrcipt_df = transcribe_audio(tmp_path)
        output = model.infer(tmp_path, transrcipt_df)

        payload = {
            "session_id": session_id,
            "uuid": user_id,
            "ve_text": output.to_csv(index=False),
        }

        # Send the result to the aggregator
        try:
            r = client.post(AGGREGATOR_URL, json=payload)
            r.raise_for_status()
        except Exception as e:
            print(f"Failed to send data to aggregator: {e}")

    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "accepted"}

