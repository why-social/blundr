import os
import shutil
import tempfile
from pathlib import Path
from threading import Lock

import httpx
from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from pandas import DataFrame

from consts import AGGREGATOR_URL, SILENCE_TOKEN
from data.audio import get_duration, is_file_silent
from model.model import Model
from model.speech_recognition import transcribe_audio

audio_processing_lock = Lock()

app = FastAPI()
model = Model(Path("/etc/model.pth"))
client = httpx.Client(timeout=None)


@app.post("/voice-emotion/predict-audio-emotion")
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

            print(f"Processing {tmp.name}")
            background_tasks.add_task(process_and_send, tmp_path, user_id, session_id)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "accepted"}


def process_and_send(file_path: Path, user_id: str, session_id: str):
    file_duration = get_duration(file_path)
    dummy_df = DataFrame(
        [
            {
                "timestamp_start": "0.00",
                "timestamp_end": f"{file_duration:.2f}",
                "sentence": SILENCE_TOKEN,
                "label": "silence",
                "confidence": 1.0,
            }
        ]
    )

    if file_duration == 0.0 or is_file_silent(file_path):
        print(f"Skipping {file_path}: File is empty or silent.")
        csv_output = dummy_df.to_csv(index=False)

    else:
        with audio_processing_lock:
            transrcipt_df = transcribe_audio(file_path)

            if transrcipt_df.empty:
                print(f"Skipping {file_path}: Transcript is empty.")
                csv_output = dummy_df.to_csv(index=False)
            else:
                output = model.infer(file_path, transrcipt_df)
                csv_output = output.to_csv(index=False)

        payload = {
            "session_id": session_id,
            "uuid": user_id,
            "ve_text": csv_output,
        }

        try:
            with httpx.Client() as client:
                r = client.post(AGGREGATOR_URL, data=payload)
                r.raise_for_status()
        except Exception as e:
            print(f"Failed to send data to aggregator: {e}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
