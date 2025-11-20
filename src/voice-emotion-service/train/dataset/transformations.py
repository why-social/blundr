import torch
import torch.nn.functional as F

def standardize_length(mel_spec, target_width):
    """
    Standardizes the time dimension of the spectrogram.
    Args:
        mel_spec: Tensor of shape (1, n_mels, time)
        target_width: The fixed number of time frames desired
    """
    _, current_width = mel_spec.shape[1], mel_spec.shape[2]

    if current_width > target_width:
        # TRUNCATE: cut the end
        # TODO: test with random cut or cutting start
        mel_spec = mel_spec[:, :, :target_width]

    elif current_width < target_width:
        # PAD: Add zeros to the end
        pad_amount = target_width - current_width
        mel_spec = F.pad(mel_spec, (0, pad_amount, 0, 0))

    return mel_spec
