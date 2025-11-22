import time
import shutil
import torch
import torchaudio

from typing import List
from dataclasses import dataclass
from pathlib import Path
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader

from dataset.transformations import standardize_length
from config.dataset_config import DatasetConfig


@dataclass
class AudioSample:
    path: Path
    filename: str
    source_dataset: str
    emotion: str
    actor: str


class SpecDataset(Dataset):
    def __init__(self,  config: DatasetConfig, samples: List[AudioSample] = []):
        self.config = config
        self.samples = samples
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)

        self.label_map = {
            'angry': 0, 'disgust': 1, 'fear': 2,
            'happy': 3, 'neutral': 4, 'sad': 5,
            'surprise': 6
        }


    def add(self, sample: AudioSample):
        self.samples.append(sample)


    def __len__(self):
        return len(self.samples)


    def _process_and_cache(self, sample):
        """The slow path: Load Audio -> Spectrogram -> Save to Disk"""
        waveform, sample_rate = torchaudio.load(sample.path)

        # resample if needed
        if sample_rate != self.config.sample_rate:
            resampler = torchaudio.transforms.Resample(
                sample_rate, 
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

        # save to Disk
        cache_dir = self.config.cache_dir/sample.emotion
        cache_dir.mkdir(parents=True, exist_ok=True)
        torch.save(spec, cache_dir/sample.filename)

        return spec


    def __getitem__(self, idx):
        sample = self.samples[idx]

        cache_path = self.config.cache_dir/sample.emotion/sample.filename
        if cache_path.exists():
            # FAST PATH: Load tensor directly
            try:
                spec = torch.load(cache_path)
            except Exception:
                # Corrupt file? Re-compute.
                spec = self._process_and_cache(sample)
        else:
            # SLOW PATH: Compute and Save
            spec = self._process_and_cache(sample)

        spec= standardize_length(spec, self.config.target_frames, mode='random')

        label_id = self.label_map.get(sample.emotion)
        assert label_id is not None

        return spec, label_id


    def preprocess(self, num_workers=4, batch_size=16):
        """
        Runs through the entire dataset, runs preprocessing and caches.
        Uses workers and DataLoader.
        """
        # dummy loader just to iterate through data
        loader = DataLoader(self, batch_size=batch_size, num_workers=num_workers, shuffle=False)

        # access every sample to trigger the cache logic
        for _ in tqdm(loader, total=len(loader), desc="Warming cache (and your computer)"):
            pass


    def dump(self, output_dir: str):
        """
        Dumps the merged dataset to a directory.
        """

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Exporting {len(self.samples)} files to {output_dir}...")

        for sample in tqdm(self.samples):
            # Format: {SOURCE}_{ORIGINAL FILENAME}.wav
            new_filename = f"{sample.source_dataset}_{sample.filename}.wav"

            dest_folder = output_path/sample.emotion

            dest_folder.mkdir(exist_ok=True)

            dest_file = dest_folder/new_filename
            shutil.copy2(sample.path, dest_file)

