from pathlib import Path

import soundfile as sf
import torch
import torchaudio
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

    def segment_to_spec(self, audio_path: Path, segment) -> torch.Tensor:
        """Partially loads an audio file and returns its spectrogram"""
        info = sf.info(str(audio_path))
        native_sr = info.samplerate
        total_frames = info.frames
        
        # Calculate target frames for the model (e.g. 3.0s * 16000)
        model_target_frames = int(self.config.target_length * native_sr)
        segment_frames = int(segment.duration * native_sr)
        
        # Determine center of the segment
        start_frame = int(segment.start_time * native_sr)
        center_frame = start_frame + (segment_frames // 2)
        
        # Determine new start/end to ensure we get exactly 3.0s
        half_window = model_target_frames // 2
        new_start = center_frame - half_window
        new_end = new_start + model_target_frames
        
        # Handle Edge Cases (Beginning/End of file)
        pad_left = 0
        pad_right = 0
        
        if new_start < 0:
            pad_left = abs(new_start)
            new_start = 0
            
        if new_end > total_frames:
            pad_right = new_end - total_frames
            new_end = total_frames
            
        # Load the Context Window
        waveform, sr = torchaudio.load(
            audio_path, frame_offset=new_start, num_frames=new_end - new_start
        )
        
        # Apply padding if we hit the edge of the file
        if pad_left > 0 or pad_right > 0:
            waveform = torch.nn.functional.pad(waveform, (pad_left, pad_right))

        return self.waveform_to_spec(waveform, sr)

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
        spec = mel_transform(waveform)  # Shape: (1, 128, time)

        db_transform = torchaudio.transforms.AmplitudeToDB()
        spec = db_transform(spec)
        return spec
