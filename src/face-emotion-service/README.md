# Face emotion recognition service

This service provides an API endpoint to process video files and report detected face emotions. Currently, the service uses ResNet34 as a backbone for face emotion classification with a custom head. For face detection, it uses a pre-trained model from OpenCV. The service is built using FastAPI and can be run using Docker or locally but is primarily intended to be deployed in a Kubernetes environment.

## Structure
- `main.py`: Main FastAPI application defining the API endpoints.
- `process_video.py`: Module containing the logic to process video files and detect face emotions.
- `models/`: Directory containing pre-trained models for face detection and custom model for face emotion classification.
- `train/`: Directory containing scripts and notebooks for training the face emotion classification model.
  - `train/train_kaggle.py`: Script to train the face emotion classification model manually with Kaggle runner. Only works on kaggle.com with T4 GPU enabled.
  - `train/train.py`: Script to train the face emotion classification model with Kubernetes jobs via admin cli commands.
- `demo/`: Directory containing scripts for running live and video file demos of the face emotion classification.
  - `demo/live_demo.py`: Script to run a live demo of the face emotion classification using webcam input.
  - `demo/videofile_demo.py`: Script to run a demo of the face emotion classification using a video file as input.

## API Endpoints
- `GET /face-emotion`: Health check endpoint.
  - **Response (JSON object)**:
	- `running`: "True"
- `POST /face-emotion/predict-face-emotion`: Endpoint to upload a video file and forward the emotions to the aggregator service.
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

### Run with Docker Compose:
```bash
docker compose up --profile serve
```

### Run with Docker:
```bash
docker build -t face-emotion-service -f Dockerfile .
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


## Training
Training can be done both manually with Kaggle and via the admin cli commands using Kubernetes jobs. Refer to [admin cli](../cli/README.md) documentation for more details on training with Kubernetes jobs. For manual training with Kaggle, use the `train/train_kaggle.py` script and ensure you have the necessary dataset available on Kaggle.

## Dataset
The model is trained on the preprocessed FER2013 and RAFDB datasets.
[Kaggle Dataset](https://www.kaggle.com/datasets/fahadullaha/facial-emotion-recognition-dataset)