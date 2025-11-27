from typing import Union

from fastapi import FastAPI, File, UploadFile
from process_video import process_video

app = FastAPI()

@app.get("/")
def read_root():
    return {"running": True}

@app.post("/predict-face-emotion")
async def process_video_endpoint(file: UploadFile = File(...)):
	result = process_video(file)
	return result