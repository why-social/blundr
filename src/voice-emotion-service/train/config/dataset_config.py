from pathlib import Path
from dataclasses import dataclass

@dataclass
class AugmentsConfig:
    # Data prep (dataset preprocessing stage)
    noise_amount: float = 0.01
    pitch_shift: int = 2
    stretch_rate: float = 0.8

    # Training (__getitem__ stage)
    freq_mask_param: int = 15  # Max vertical bins to mask in spectrogram (out of 128)
    time_mask_param: int = 35  # Max time frames to mask in spectrogram

    # Toggles
    dataset_aug_enabled: bool = True
    spec_aug_enabled: bool = True


@dataclass
class DatasetConfig:
    sample_rate: int = 16000 # Hz
    n_mels: int = 128 # resolution of the spectrogram - how many 'rows'
    target_length: float = 3.0 # seconds
    hop_length: int = 512
    n_fft: int = hop_length * 2
    cache_dir: Path = Path("./.cache")
    raw_data_dir: Path = Path("./.raw_datasets")

    @property
    def target_frames(self) -> int:
        """
        Automatically converts seconds to spectrogram frames.
        """
        return int((self.target_length * self.sample_rate) / self.hop_length)
