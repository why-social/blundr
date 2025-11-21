import os
import torch
import torchaudio
from pathlib import Path
from tqdm import tqdm

from config.dataset_config import AugmentsConfig
from dataset import transformations

def augment_dataset(datasets, config: AugmentsConfig):
    for dataset_name, path in datasets.items():
        for root, _, files in os.walk(path):
            if not any(f.lower().endswith(".wav") for f in files): continue

            for file in tqdm(files, desc=f"Augmenting dataset {dataset_name} ({root})"):
                if not file.lower().endswith('.wav'): continue

                root = Path(root)

                orig_waveform, sample_rate = torchaudio.load(root/file)
                base_name = file.replace('.wav', '')

                if amount := config.noise_amount != 0:
                    aug_file = root/f"{base_name}_noise.wav"
                    if not aug_file.exists():
                        waveform = transformations.add_white_noise(orig_waveform, amount)
                        torchaudio.save(aug_file, waveform, sample_rate)

                if n_steps := config.pitch_shift != 0:
                    aug_file = root/f"{base_name}_pitch.wav"
                    if not aug_file.exists():
                        waveform = orig_waveform.detach().cpu().numpy()
                        waveform = transformations.pitch_shift(waveform, sample_rate, n_steps)
                        if waveform.ndim == 1:
                            waveform = waveform[None, :]
                        waveform = torch.from_numpy(waveform)
                        torchaudio.save(aug_file, waveform, sample_rate)

                if rate := config.stretch_rate != 0:
                    aug_file = root/f"{base_name}_stretch.wav"
                    if not aug_file.exists():
                        waveform = orig_waveform.detach().cpu().numpy()
                        waveform = transformations.time_stretch(waveform, rate)
                        if waveform.ndim == 1:
                            waveform = waveform[None, :]
                        waveform = torch.from_numpy(waveform)
                        torchaudio.save(aug_file, waveform, sample_rate)


