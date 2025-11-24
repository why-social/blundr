import torch
import torchaudio
import numpy as np
from pathlib import Path
from common.config.dataset_config import DatasetConfig

class AudioProcessor:
    def __init__(self, config: DatasetConfig):
        self.config = config
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=config.sample_rate,
            n_mels=config.n_mels,
            hop_length=config.hop_length,
            n_fft=config.n_fft,
        )
        self.db_transform = torchaudio.transforms.AmplitudeToDB()

    def file_to_spec(self, path: Path) -> torch.Tensor:
        """Reads a file and returns a Spectrogram Tensor"""
        waveform, sr = torchaudio.load(path)
        return self.waveform_to_spec(waveform, sr)

    def mic_data_to_spec(self, audio_data: np.ndarray) -> torch.Tensor:
        """Takes raw numpy audio (from pyaudio/sounddevice) and returns Spec"""
        waveform = torch.from_numpy(audio_data).float()
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0) # Add channel dim
        return self.waveform_to_spec(waveform, self.config.sample_rate)

    def waveform_to_spec(self, waveform: torch.Tensor, sr: int) -> torch.Tensor:
        # resample if needed
        if sr != self.config.sample_rate:
            resampler = torchaudio.transforms.Resample(
                sr, 
                self.config.sample_rate,
            )
            waveform = resampler(waveform)

        # to mono
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)


        # generate spectrogram
        mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.config.sample_rate,
            n_mels=self.config.n_mels,
            hop_length=self.config.hop_length,
            n_fft=self.config.n_fft,
        )
        spec = mel_transform(waveform) # Shape: (1, 128, time)

        db_transform = torchaudio.transforms.AmplitudeToDB()
        spec = db_transform(spec)
        return spec
