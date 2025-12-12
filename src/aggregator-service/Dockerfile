FROM python:3.11-slim

WORKDIR /src/aggregator-service

RUN apt-get update && apt-get install build-essential -y curl ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn requests pandas python-multipart httpx

COPY . .

ENTRYPOINT [ "uvicorn", "Main:app", "--host", "0.0.0.0", "--port", "42069" ]

