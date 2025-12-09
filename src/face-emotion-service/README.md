# Face emotion classification service

This service provides an API endpoint to process video files and report detected face emotions.

Current pretrained model: ResNet34
Current exposed port: 42069

## API Endpoints
- `POST /predict-face-emotion`: Endpoint to upload a video file and forward the emotions to the aggregator service.
  - **Parameters (Form Data)**:
	- `file`: Video file to be processed. (webm format)
	- `user_id`: Identifier for the user uploading the video.
	- `session_id`: Identifier for the session.
  - **Response (JSON object)**:
	- `status`: Status of the processing (e.g., "accepted").

Example Response:
```json
{
  "status": "accepted"
}
```

## Running the Service

### Run with Docker:
```bash
docker build -t face-emotion-service .
docker run -d -p 42069:42069 face-emotion-service
```

### Run locally:
Install dependencies:

```bash
pip install -r requirements.txt
```

Run the service:

```bash
uvicorn main:app --host localhost --port 42069
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