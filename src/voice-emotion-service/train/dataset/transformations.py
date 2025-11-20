import torch
import torch.nn.functional as F
from numpy.random import randint

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
