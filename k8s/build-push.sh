# Original Author: Aliaksei Khval
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT
#!/bin/bash
set -e  # Exit on any error

# Usage check
if [ $# -ne 1 ]; then
  echo "Usage: $0 <service_name>"
  echo "Available services: fer, ver, aggregator, admin, trainer"
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
  admin)
    SERVICE_NAME="admin-api"
    BUILD_CONTEXT="$PROJECT_ROOT/src/admin-api"
    ;;
  trainer)
    SERVICE_NAME="fer-train"
    BUILD_CONTEXT="$PROJECT_ROOT/src/face-emotion-service"
    DOCKERFILE="Dockerfile.train"
    ;;
  *)
    echo "Error: Unknown service '$SERVICE_NAME'. Valid options: fer, ver, aggregator, admin, trainer"
    exit 1
    ;;
esac

: "${DOCKERFILE:=Dockerfile}" # set to default Dockerfile if unset

# Build Docker image
DOCKER_BUILDKIT=1
docker buildx build \
  --platform linux/amd64 \
  -f "$BUILD_CONTEXT/$DOCKERFILE" \
  -t ${KUBE_REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:v1 \
  -t ${KUBE_REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest \
  "$BUILD_CONTEXT" --push

echo "Docker images for '$SERVICE_NAME' built and pushed successfully."
