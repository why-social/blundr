from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from process_video import process_video
from typing import Annotated
import httpx, tempfile, shutil, os

app = FastAPI()

AGGREGATOR_URL = os.environ.get("AGGREGATOR_URL", "http://localhost:42069/aggregator")
TIMEOUT_FOR_AGGREGATOR_SERVICE = 10.0

@app.get("/")
def read_root():
	return {"running": True}

# Asynchronous function to process video and send results
def process_and_send(file_path: str, user_id: str, session_id: str):
	try:
		# Process the video
		log = process_video(file_path)

		payload = {
			"session_id": session_id,
			"uuid": user_id,
			"fe_text": log
		}

		# Send the result to the aggregator
		with httpx.Client(timeout=TIMEOUT_FOR_AGGREGATOR_SERVICE) as client:
			try:
				r = client.post(AGGREGATOR_URL, data=payload)
				r.raise_for_status()
				print("Data sent to aggregator successfully.")
			except Exception as e:
				print(f"Failed to send data to aggregator: {e}")
	finally:
		if os.path.exists(file_path):
			os.remove(file_path)

@app.post("/predict-face-emotion")
async def process_video_endpoint(
	background_tasks: BackgroundTasks,
	user_id: Annotated[str, Form(...)],
	session_id: Annotated[str, Form(...)],
	file: UploadFile = File(...)
):
	try:
		print(f"Received file: {file.filename} for user_id: {user_id}, session_id: {session_id}")
		print("Saving uploaded file to temporary location...")
		# Save the uploaded file to a temporary location
		with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
			shutil.copyfileobj(file.file, tmp)
			tmp_path = tmp.name
			print(f"File saved to {tmp_path}")

		# Schedule the processing task in the background
		print("Scheduling background task for processing and sending data...")
		background_tasks.add_task(process_and_send, tmp_path, user_id, session_id)
	except Exception as e:
		return {"status": "error", "message": str(e)}
	
	# Return an acknowledgment response
	return {"status": "accepted"}