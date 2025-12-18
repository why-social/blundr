import os

AGGREGATOR_URL = os.environ.get("AGGREGATOR_URL", "http://localhost:42069/aggregator")
MODEL_PATH = os.environ.get("MODEL_PATH", "/etc/model.pth")
SILENCE_TOKEN = ". . ."
MIN_PAUSE = 0.2
