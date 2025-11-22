from pathlib import Path
from dataclasses import dataclass

from dataset.transformations import pitch_shift

@dataclass
class AugmentsConfig:
    noise_amount: float = 0.01 
    pitch_shift: int = 0
    stretch_rate: float = 0

    @property
    def enabled(self) -> bool:
        return self.noise_amount != 0 and self.pitch_shift != 0 and self.stretch_rate != 0

@dataclass
class DatasetConfig:
    sample_rate: int = 16000 # Hz
    n_mels: int = 128 # resolution of the spectrogram - how many 'rows'
    target_length: float = 3.0 # seconds
    hop_length: int = 512
    n_fft: int = hop_length * 2
    cache_dir: Path = Path("./.cache")
    raw_data_dir: Path = Path("./raw_datasets")


    @property
    def target_frames(self) -> int:
        """
        Automatically converts seconds to spectrogram frames.
        """
        return int((self.target_length * self.sample_rate) / self.hop_length)
