# Face emotion classification service

This service provides API endpoints for receiving information to aggregate and for requests to send the analysis back to the requesting user(s).


## API Endpoints
- `POST /aggregator/aggregator`: Endpoint that receives emotion data from voice and face emotion services, to then aggregate them into a single file.
  - **Parameters (Form Data)**:
	- `session_id`: Identifier for the session.
	- `uuid`: Identifier for the user which is in the video or audio data.
    - `fe_text`: Information containing the facial emotion of the user (uuid).
    - `ve_text`: Information containing the voice emotion of the user as well as transcription (uuid).
  - **Response (JSON object)**:
	- `status`: Status of the processing (waiting for other parts) or the final aggregated output.

Example Response:
```json
{
  "status": "waiting for other part(s)"
}
```
- `GET /aggregator/analyze`: Endpoint that sends the analysis performed by the LLM on final aggregated output, if available.
  - **Parameters (Query Parameters)**:
	- `user_id`: Identifier for the user requesting their analysis.
	- `session_id`: Identifier for the session.
  - **Response (JSON object)**:
	- `status`: Status of the processing (e.g., "processing") or the completed analysis for the user.

Example Response:
```json
{
  "session_id": session_id,
  "requested_by": user_id,
  "status": "processing",
  "analysis": None
}
```

## Running the Service

### Run with Docker:
```bash
docker build -f Dockerfile.local-ollama -t aggregator .
docker run --gpus all -p 11434:11434 -p 42069:42069 aggregator
```

### Run locally:
Install dependencies:
```bash
pip install fastapi uvicorn requests pandas python-multipart httpx
```
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Run the service:

```bash
// Terminal 1
ollama serve
```
```bash
// Terminal 2
ollama pull qwen2.5:7b
```
```bash
// Terminal 3
uvicorn main:app --host localhost --port 42069
```

## Structure
- `main.py`: Main FastAPI application defining the API endpoints.
- `aggregator.py`: Module containing the logic to aggregate voice and face emotion data.
