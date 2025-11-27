import os
from pathlib import Path

import torch
import torchaudio
from common.config.dataset_config import AugmentsConfig
from common.utils import transformations
from tqdm import tqdm


def augment_dataset(datasets, config: AugmentsConfig) -> None:
    if not config.dataset_aug_enabled:
        print("No enabled augmentations in config. Skipping")
        return

    for dataset_name, path in datasets.items():
        for root, _, files in os.walk(path):
            if not any(f.lower().endswith(".wav") for f in files):
                continue

            for file in tqdm(files, desc=f"Augmenting dataset {dataset_name} ({root})"):
                if not file.lower().endswith(".wav"):
                    continue

                root = Path(root)
                base_name = file.replace(".wav", "")

                if base_name.endswith(("_pitch", "_noise", "_stretch")):
                    continue

                aug_targets = []
                if config.noise_amount != 0:
                    aug_file = root / f"{base_name}_noise.wav"
                    if not aug_file.exists():
                        aug_targets.append(("noise", aug_file))

                if config.pitch_shift != 0:
                    aug_file = root / f"{base_name}_pitch.wav"
                    if not aug_file.exists():
                        aug_targets.append(("pitch", aug_file))

                if config.stretch_rate != 0:
                    aug_file = root / f"{base_name}_stretch.wav"
                    if not aug_file.exists():
                        aug_targets.append(("stretch", aug_file))

                if not aug_targets:
                    continue

                orig_waveform, sample_rate = torchaudio.load(root / file)
                for aug_type, aug_path in aug_targets:
                    if aug_type == "noise":
                        waveform = transformations.add_white_noise(
                            orig_waveform, config.noise_amount
                        )
                        torchaudio.save(aug_path, waveform, sample_rate)

                    elif aug_type == "pitch":
                        waveform = orig_waveform.detach().cpu().numpy()
                        waveform = transformations.pitch_shift(
                            waveform, sample_rate, config.pitch_shift
                        )
                        if waveform.ndim == 1:
                            waveform = waveform[None, :]
                        waveform = torch.from_numpy(waveform)
                        torchaudio.save(aug_path, waveform, sample_rate)

                    elif aug_type == "stretch":
                        waveform = orig_waveform.detach().cpu().numpy()
                        waveform = transformations.time_stretch(
                            waveform, config.stretch_rate
                        )
                        if waveform.ndim == 1:
                            waveform = waveform[None, :]
                        waveform = torch.from_numpy(waveform)
                        torchaudio.save(aug_path, waveform, sample_rate)
