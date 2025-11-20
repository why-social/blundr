import shutil

from typing import List
from dataclasses import dataclass
from pathlib import Path
from tqdm import tqdm

@dataclass
class AudioSample:
    path: Path
    filename: str
    source_dataset: str
    emotion: str


class Dataset:
    def __init__(self):
        self.samples: List[AudioSample] = []


    def add(self, sample: AudioSample):
        self.samples.append(sample)


    def __len__(self):
        return len(self.samples)


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
