import torch
import torch.nn.functional as F
import numpy as np
from numpy.random import randint
from librosa import effects

def standardize_length(mel_spec, target_frames, mode='end'):
    """
    Standardizes the time dimension of the spectrogram.
    Args:
        mel_spec: Tensor of shape (1, n_mels, time)
        target_frames: The fixed number of time frames desired
        mode: Truncation mode - 'end' or 'random'. Default - 'end'
    """
    n_mels, current_frames = mel_spec.shape[1], mel_spec.shape[2]

    if current_frames > target_frames:
        # TRUNCATE: at the end or randomly
        if mode == 'end':
            mel_spec = mel_spec[:, :, :target_frames]
        else:
            if mode != 'random':
                print(f"WARNING: standardize_length(): mode '{mode}' is invalid. Using 'random'.")
            start = randint(0, current_frames - target_frames)
            mel_spec = mel_spec[:, :, start : start + target_frames]

    elif current_frames < target_frames:
        # PAD: Add zeros to the end
        pad_amount = target_frames - current_frames
        mel_spec = F.pad(mel_spec, (0, pad_amount, 0, 0))

    return mel_spec


def add_white_noise(waveform, noise_level=0.005):
    if noise_level <= 0.0:
        print(f"ERROR: add_white_noise(): noise_level must be > 0.0. Skipping.")
        return

    noise = randint(len(waveform))
    augmented = waveform + noise_level * noise
    return augmented


def time_stretch(waveform, rate=0.8):
    """
    Stretches the waveform time.
    Note: This changes the array length!
    """
    if rate <= 0.0:
        print(f"ERROR: time_stretch(): rate must be > 0.0. Skipping.")
        return waveform

    if abs(1-rate) > 0.2:
        print(f"WARNING: time_stretch(): rate {rate} is too large/small (recommended between 0.8 and 1.2). Risking data loss.")
    return effects.time_stretch(y=waveform, rate=rate)

def pitch_shift(waveform, sr, n_steps=2):
    """
    Shifts the pitch by `n_steps` semitiones.
    sr - sample rate
    """
    if n_steps == 0:
        print(f"ERROR: pitch_shift(): n_steps must be != 0. Skipping.")
        return waveform

    if abs(n_steps) > 2:
        print(f"WARNING: pitch_shift(): shifting by too many semitiones (recommended <= 2). Risking misclassification.")
    return effects.pitch_shift(y=waveform, sr=sr, n_steps=n_steps)

