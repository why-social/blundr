import torch
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DatasetConfig:
    sample_rate: int = 16000 # Hz
    n_mels: int = 128 # resolution of the spectrogram - how many 'rows'
    target_length: float = 3.0 # seconds
    hop_length: int = 512
    n_fft: int = hop_length * 2
    cache_dir: Path = Path("./.cache")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    @property
    def target_frames(self) -> int:
        """
        Automatically converts seconds to spectrogram frames.
        """
        return int((self.target_length * self.sample_rate) / self.hop_length)
