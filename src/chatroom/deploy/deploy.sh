#!/bin/bash
set -e
set -o pipefail

TAG="${1:-latest}"

if [ -n "$TAG" ]; then
    IMAGE="europe-north2-docker.pkg.dev/blundr/blundr-repo/chatroom:$TAG"
else
    IMAGE="europe-north2-docker.pkg.dev/blundr/blundr-repo/chatroom"
fi

SERVICE_NAME="chatroom"

echo "Authenticating Docker with GCP Artifact Registry..."
gcloud auth configure-docker europe-north2-docker.pkg.dev --quiet

echo "Pulling latest Docker image..."
docker pull $IMAGE

echo "Stopping existing container (if running)..."
sudo systemctl stop chatroom.service || true

echo "Removing old container (if exists)..."
sudo docker rm chatroom || true

echo "Starting the service..."
sudo systemctl start chatroom.service

echo "Deployment completed successfully!"
