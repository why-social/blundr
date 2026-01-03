# Original Author: Maxine Orlen
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT

import os
import subprocess
from pathlib import Path


def _dataset_already_downloaded(out_dir: Path) -> bool:
    """Return True if out_dir already has wav files."""
    if not out_dir.exists():
        return False

    for _, _, files in os.walk(out_dir):
        if any(f.lower().endswith(".wav") for f in files):
            return True

    return False


def _download_dataset(name, path, force):
    print(f"Downloading {name}...")
    out_dir = Path(path) / name.replace("/", "_")
    out_dir.mkdir(parents=True, exist_ok=True)

    if _dataset_already_downloaded(out_dir):
        if not force:
            print("Dataset already present. Skipping.")
            return out_dir

    url = f"https://www.kaggle.com/api/v1/datasets/download/{name}"
    zip_path = out_dir / "dataset.zip"

    subprocess.run(["curl", "-L", "-o", str(zip_path), url], check=True)

    subprocess.run(["unzip", "-o", str(zip_path), "-d", str(out_dir)], check=True)
    subprocess.run(["rm", "-fr", str(zip_path)], check=True)

    return out_dir


def download_datasets(path, force=False):
    datasets = {
        "CREMA": _download_dataset("ejlok1/cremad", path, force),
        "RAVDESS": _download_dataset(
            "uwrfkaggler/ravdess-emotional-speech-audio", path, force
        ),
        "SAVEE": _download_dataset("barelydedicated/savee-database", path, force),
        "TESS": _download_dataset(
            "ejlok1/toronto-emotional-speech-set-tess", path, force
        ),
    }

    raw_files_set = set()
    for source_name, path in datasets.items():
        for root, _, files in os.walk(path):
            for file in files:
                if file.lower().endswith(".wav"):
                    # Store absolute path to ensure matching is accurate
                    full_path = str(Path(root) / file).strip()
                    raw_files_set.add(full_path)
    print(f"Raw dataset files: {len(raw_files_set)}")

    return datasets
