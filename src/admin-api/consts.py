import os
from pathlib import Path

ENDPOINT_PREFIX = "/admin"

# GCS mounts
DATA_MOUNT_ROOT = Path(os.getenv("DATA_ROOT", "/data"))
CAS_DIR_NAME = "cas"
CAS_ROOT = DATA_MOUNT_ROOT / CAS_DIR_NAME
BATCH_ROOT = DATA_MOUNT_ROOT / "batches"

CAS_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_ROOT.mkdir(parents=True, exist_ok=True)

MODELS_MOUNT_ROOT = Path(os.getenv("MODELS_ROOT", "/models"))

FER_DEPLOYMENT = {
    "DEPLOYMENT_NAME": "fer",
    "NAMESPACE": "default",
    "CONTAINER_NAME": "fer",
    "ENV_VAR_NAME": "MODEL_PATH",
    "VOLUME_NAME_KEY": "gcs-fer-model-bucket",
    "NODEPOOL_NAME": "kiddie-pool",
}

GCS_MODEL_BUCKET_NAME = "blundr-fer-models"
GCS_DATA_BUCKET_NAME = "blundr-fer-data"

GCS_MOUNTS = {
    GCS_MODEL_BUCKET_NAME: MODELS_MOUNT_ROOT,
    GCS_DATA_BUCKET_NAME: DATA_MOUNT_ROOT,
}

MODEL_FILENAME = "fer_model.pt"

FER_TRAIN_IMAGE = "europe-north2-docker.pkg.dev/blundr/blundr-repo/fer-train:latest"
