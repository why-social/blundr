import shutil
import torch
import torchaudio

from typing import List
from dataclasses import dataclass
from pathlib import Path
from tqdm import tqdm

from transformations import standardize_length

@dataclass
class AudioSample:
    path: Path
    filename: str
    source_dataset: str
    emotion: str


class Dataset:
    def __init__(self, target_length=300):
        self.target_length = target_length
        self.samples: List[AudioSample] = []

        self.label_map = {
            'neutral': 0,
            'happy': 1,
            'sad': 2,
            'anger': 3,
            'fear': 4,
            'disgust': 5,
            'surprise': 6
        }


    def add(self, sample: AudioSample):
        self.samples.append(sample)


    def __len__(self):
        return len(self.samples)


    def __getitem__(self, idx):
        assert idx < self.__len__()

        sample = self.samples[idx]

        waveform, _ = torchaudio.load(sample.path)

        mel_transform = torchaudio.transforms.MelSpectrogram(sample_rate=16000, n_mels=128)
        spectrogram = mel_transform(waveform) # Shape: (1, 128, time)

        spectrogram = standardize_length(spectrogram, self.target_length)

        label_id = self.label_map[sample.emotion]

        return spectrogram, label_id


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
