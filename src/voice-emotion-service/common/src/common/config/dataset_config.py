from pathlib import Path
from dataclasses import dataclass
from typing import Dict


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
    sample_rate: int = 16000  # Hz
    n_mels: int = 128  # resolution of the spectrogram - how many 'rows'
    target_length: float = 3.0  # seconds
    hop_length: int = 512
    n_fft: int = hop_length * 2
    cache_dir: Path = Path("./.cache")
    raw_data_dir: Path = Path("./.raw_datasets")

    label_map = {
        "angry": 0,
        "disgust": 1,
        "fear": 2,
        "happy": 3,
        "neutral": 4,
        "sad": 5,
        # 'surprise': 6
    }

    @property
    def target_frames(self) -> int:
        """
        Automatically converts seconds to spectrogram frames.
        """
        return int((self.target_length * self.sample_rate) / self.hop_length)

    @property
    def n_classes(self) -> int:
        return len(self.label_map)

    @property
    def label_map_reverse(self) -> Dict[int, str]:
        return {v: k for k, v in self.label_map.items()}
