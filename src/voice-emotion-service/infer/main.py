from pathlib import Path

import httpx
import shutil
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from model.model import Model
from model.speech_recognition import transcribe_audio
import os
from threading import Lock 

audio_processing_lock = Lock()

AGGREGATOR_URL = os.environ.get("AGGREGATOR_URL", "http://localhost:42069/aggregator")

app = FastAPI()
model = Model(Path("/etc/model.pth"))


@app.post("/predict-audio-emotion")
async def infer(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    user_id: str = Form(...),
    audio: UploadFile = File(...),
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            shutil.copyfileobj(audio.file, tmp)
            tmp_path = Path(tmp.name)

            background_tasks.add_task(process_and_send, tmp_path, user_id, session_id)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "accepted"}


def process_and_send(file_path: Path, user_id: str, session_id: str):
    try:
        with audio_processing_lock:
            transrcipt_df = transcribe_audio(file_path)
            output = model.infer(file_path, transrcipt_df)

        payload = {
            "session_id": session_id,
            "uuid": user_id,
            "ve_text": output.to_csv(index=False),
        }

        # Send the result to the aggregator
        try:
            with httpx.Client() as client:
                r = client.post(AGGREGATOR_URL, data=payload)
                r.raise_for_status()
        except Exception as e:
            print(f"Failed to send data to aggregator: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

