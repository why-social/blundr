FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY process_video.py .
COPY models/ ./models/

EXPOSE 42069

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "42069"]