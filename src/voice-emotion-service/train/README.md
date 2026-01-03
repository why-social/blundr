# ve-train

This module contains the training script for the VER model.

The flow is as follows:
1. data is downloaded from kaggle into `.raw_datasets/` (if not already present)
2. raw data (audio) is transformed into spectrograms and saved into `.cache/` (for each datapoint not present)
3. the model is trained and saved as `out/model.pth`


## Updating model at runtime

Updating the VER model in the deployment must be done manually:

1. Upload the new model to the GCS bucket `blundr-ver-models` as `model.pth`
NOTE: follow a convention of `/models/vX/model.pth` for the path.

2. Run `kubectl set env deployment/ver MODEL_PATH=<PATH>`
, where `<PATH>` is the full path to the .pth file in the bucket.


