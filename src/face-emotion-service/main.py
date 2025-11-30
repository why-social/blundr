from typing import Union

from fastapi import FastAPI, File, UploadFile, Form
from process_video import process_video
from typing import Annotated

app = FastAPI()

@app.get("/")
def read_root():
    return {"running": True}

@app.post("/predict-face-emotion")
async def process_video_endpoint(
	user_id: Annotated[str, Form(...)],
	session_id: Annotated[str, Form(...)],
	file: UploadFile = File(...)
):
	emotions = process_video(file)
	return {
		"user_id": user_id,
		"session_id": session_id,
		"result": emotions
	}