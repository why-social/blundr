import kagglehub
import os
from pathlib import Path

def download_crema():
    path = kagglehub.dataset_download("ejlok1/cremad")
    return Path(path)

def download_ravdess():
    path = kagglehub.dataset_download("uwrfkaggler/ravdess-emotional-speech-audio")
    return Path(path)

def download_savee():
    path = kagglehub.dataset_download("barelydedicated/savee-database")
    return Path(path)

def download_tess():
    path = kagglehub.dataset_download("ejlok1/toronto-emotional-speech-set-tess")
    return Path(path)

def download_all():
    datasets = {
        "CREMA": download_crema(),
        "RAVDESS": download_ravdess(),
        "SAVEE": download_savee(),
        "TESS": download_tess(),
    }

    raw_files_set = set()
    for source_name, path in datasets.items():
        for root, _, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.wav'):
                    # Store absolute path to ensure matching is accurate
                    full_path = str(Path(root) / file).strip()
                    raw_files_set.add(full_path)
    print(f"Raw dataset files: {len(raw_files_set)}")

    return datasets

