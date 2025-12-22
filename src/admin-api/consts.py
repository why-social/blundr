from pathlib import Path
import os

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
}

MODEL_FILENAME = 'emotion_model.pt'
