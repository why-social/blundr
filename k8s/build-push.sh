#!/bin/bash
set -e  # Exit on any error

# Usage check
if [ $# -ne 1 ]; then
  echo "Usage: $0 <service_name>"
  echo "Available services: fer, ver, aggregator"
  exit 1
fi

SERVICE_NAME=$1

# Project and repo configuration
PROJECT_ID="blundr"
REPO_NAME="blundr-repo"
KUBE_REGION="europe-north2"

# Determine project root dynamically
PROJECT_ROOT=$(git rev-parse --show-toplevel)
if [ -z "$PROJECT_ROOT" ]; then
  echo "Error: Could not determine project root. Make sure this is inside a Git repo."
  exit 1
fi

# Map service names to build directories
case "$SERVICE_NAME" in
  fer)
    BUILD_CONTEXT="$PROJECT_ROOT/src/face-emotion-service"
    ;;
  ver)
    BUILD_CONTEXT="$PROJECT_ROOT/src/voice-emotion-service"
    ;;
  aggregator)
    BUILD_CONTEXT="$PROJECT_ROOT/src/aggregator-service"
    ;;
  *)
    echo "Error: Unknown service '$SERVICE_NAME'. Valid options: fer, ver, aggregator"
    exit 1
    ;;
esac

# Build Docker image
docker buildx build \
  --platform linux/amd64 \
  -t ${KUBE_REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:v1 \
  -t ${KUBE_REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest \
  "$BUILD_CONTEXT"

# Push Docker image
docker push ${KUBE_REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:v1
docker push ${KUBE_REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest

echo "Docker images for '$SERVICE_NAME' built and pushed successfully."
