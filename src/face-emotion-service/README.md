# Face emotion classification service

This service provides an API endpoint to process video files and report detected face emotions.

## API Endpoints
- `POST /predict-face-emotion`: Endpoint to upload a video file and receive detected face emotions.
  - **Parameters (Form Data)**:
	- `file`: Video file to be processed. (mp4)
	- `user_id`: Identifier for the user uploading the video.
	- `session_id`: Identifier for the session.
  - **Response (JSON object)**:
	- `user_id`: The user ID provided in the request.
	- `session_id`: The session ID provided in the request.
	- `result`: Detected face emotions from the video.
	  - `status`: Status of the processing ("processed" or "error").
	  - `message`: A string containing the list of emotions in .csv format

Example Response:
```json
{
  "user_id": "user123",
  "session_id": "session123",
  "result": {
	"status": "processed",
	"message": "time,emotion\n0.00,happy\n0.50,happy\n1.00,happy\n1.50,happy\n"
  }
}
```

## Running the Service

### Run with Docker:
```bash
docker build -t face-emotion-service .
docker run -d -p 8000:8000 face-emotion-service
```

### Run locally:

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the service:

```bash
uvicorn main:app --host localhost --port 8000
```

## Structure
- `main.py`: Main FastAPI application defining the API endpoints.
- `process_video.py`: Module containing the logic to process video files and detect face emotions.
- `models/`: Directory containing pre-trained models for face detection and custom model for face emotion classification.
- `train/`: Directory containing scripts and notebooks for training the face emotion classification model.
- `demo/`: Directory containing scripts for running live and video file demos of the face emotion classification.


## Training and Demo Scripts
- `train/train_kaggle.py`: Script to train the face emotion classification model with Kaggle runner. Only works on kaggle.com with T4 GPU enabled.
- `demo/live_demo.py`: Script to run a live demo of the face emotion classification using webcam input.
- `demo/videofile_demo.py`: Script to run a demo of the face emotion classification using a video file as input.