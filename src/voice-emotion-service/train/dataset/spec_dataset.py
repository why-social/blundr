import shutil
import torch
import torchaudio
import torchaudio.transforms as T

from typing import List
from dataclasses import dataclass
from pathlib import Path
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader

from common.utils.transformations import standardize_length
from common.config.dataset_config import AugmentsConfig, DatasetConfig
from common.utils.audio_processing import AudioProcessor


@dataclass
class AudioSample:
    path: Path
    filename: str
    source_dataset: str
    emotion: str
    actor: str


class SpecDataset(Dataset):
    def __init__(
        self,
        data_config: DatasetConfig,
        aug_config: AugmentsConfig,
        samples: List[AudioSample] = [],
        is_train: bool = False,
    ):
        self.data_config = data_config
        self.aug_config = aug_config
        self.samples = samples
        self.is_train = is_train

        self.data_config.cache_dir.mkdir(parents=True, exist_ok=True)

        self.processor = AudioProcessor(data_config)

        # prepare transformations if enabled
        if self.aug_config.spec_aug_enabled:
            self.freq_mask = T.FrequencyMasking(
                freq_mask_param=self.aug_config.freq_mask_param
            )
            self.time_mask = T.TimeMasking(
                time_mask_param=self.aug_config.time_mask_param
            )

    def add(self, sample: AudioSample):
        self.samples.append(sample)

    def __len__(self):
        return len(self.samples)

    def _process_and_cache(self, sample):
        """The slow path: Load Audio -> Spectrogram -> Save to Disk"""
        waveform, sample_rate = torchaudio.load(sample.path)

        spec = self.processor.waveform_to_spec(waveform, sample_rate)

        # save to Disk
        cache_dir = self.data_config.cache_dir / sample.emotion
        cache_dir.mkdir(parents=True, exist_ok=True)
        torch.save(spec, cache_dir / sample.filename)

        return spec

    def __getitem__(self, idx):
        sample = self.samples[idx]

        cache_path = self.data_config.cache_dir / sample.emotion / sample.filename
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

        spec = standardize_length(spec, self.data_config.target_frames, mode="random")

        if self.is_train and self.aug_config.spec_aug_enabled:
            spec = self.freq_mask(spec)
            spec = self.time_mask(spec)

        label_id = self.data_config.label_map.get(sample.emotion)
        assert label_id is not None

        return spec, label_id

    def preprocess(self, num_workers=4, batch_size=16):
        """
        Runs through the entire dataset, runs preprocessing and caches.
        Uses workers and DataLoader.
        """
        # dummy loader just to iterate through data
        loader = DataLoader(
            self, batch_size=batch_size, num_workers=num_workers, shuffle=False
        )

        # access every sample to trigger the cache logic
        for _ in tqdm(
            loader, total=len(loader), desc="Warming cache (and your computer)"
        ):
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

            dest_folder = output_path / sample.emotion

            dest_folder.mkdir(exist_ok=True)

            dest_file = dest_folder / new_filename
            shutil.copy2(sample.path, dest_file)
