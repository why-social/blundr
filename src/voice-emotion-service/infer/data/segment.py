# Original Author: Maxine Orlen
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from common.config.dataset_config import DatasetConfig
from consts import SILENCE_TOKEN


@dataclass
class TranscribedSegment:
    sentence_idx: int
    start_time: float
    end_time: float
    label: str = "unknown"

    @property
    def duration(self):
        return self.end_time - self.start_time


def load_transcribed_segments(
    transcript: pd.DataFrame, audio_path: Path, config: DatasetConfig
) -> List[TranscribedSegment]:
    """
    Reads CSV and splits speaking sections into chunks matching the maximum size
    from `DatasetConfig`, and optimising for minimal padding.
    """
    assert audio_path.exists(), f"ERROR: Audio file not found: {audio_path}"
    assert not transcript.empty, "ERROR: Empty transcript"

    print(
        f"INFO [load_transcribed_segments()]: loaded {len(transcript.index)} transcription entries"
    )
    chunks = []

    # Iterate through every speaking turn
    for idx, (_, row) in enumerate(transcript.iterrows()):
        t_start = float(row["timestamp_start"])
        t_end = float(row["timestamp_end"])
        duration = t_end - t_start

        target_sec = config.target_length

        if str(row["sentence"]) == SILENCE_TOKEN:
            continue  # skip silences

        if duration <= target_sec:
            chunks.append(TranscribedSegment(idx, t_start, t_end))
        else:
            # split equally to minimize padding
            num_chunks = int(np.ceil(duration / target_sec))
            chunk_len = duration / num_chunks

            for i in range(num_chunks):
                chunk_start = t_start + (i * chunk_len)
                chunk_end = chunk_start + chunk_len

                chunks.append(TranscribedSegment(idx, chunk_start, chunk_end))

    return chunks
