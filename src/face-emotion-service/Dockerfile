FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY main.py .
COPY process_video.py .

EXPOSE 42069

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "42069"]
