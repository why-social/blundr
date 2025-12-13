from pathlib import Path

import soundfile as sf
import torchaudio


def get_duration(path: Path) -> float:
    try:
        info = sf.info(str(path))
        return info.duration
    except Exception:
        return 0.0

def is_file_silent(path: Path, threshold: float = 1e-4) -> bool:
    """Returns True if file is purely silent, or cannot be opened."""
    try:
        wav, _ = torchaudio.load(path)
        if wav.numel() == 0:
            return True

        if wav.abs().max() < threshold:
            return True

        return False
    except Exception as e:
        print(f"Error checking file {path}: {e}")
        return True
