import kagglehub
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
    return {
        "CREMA": download_crema(),
        "RAVDESS": download_ravdess(),
        "SAVEE": download_savee(),
        "TESS": download_tess(),
    }

