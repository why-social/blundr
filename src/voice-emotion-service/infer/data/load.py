from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from common.config.dataset_config import DatasetConfig
from data.segment import TranscribedSegment


def load_transcribed_segments(
    csv_path: Path, audio_path: Path, config: DatasetConfig
) -> List[TranscribedSegment]:
    """
    Reads CSV and splits speaking sections into chunks matching the maximum size
    from `DatasetConfig`, and optimising for minimal padding.
    """
    assert csv_path.exists(), f"ERROR: Transcription file not found: {csv_path}"
    assert audio_path.exists(), f"ERROR: Audio file not found: {audio_path}"

    df = pd.read_csv(csv_path)
    segments = []

    # Iterate through every speaking turn
    for _, row in df.iterrows():
        t_start = float(row["timestamp_start"])
        t_end = float(row["timestamp_end"])
        duration = t_end - t_start

        target_sec = config.target_length

        if duration <= target_sec:
            segments.append(TranscribedSegment(audio_path, t_start, t_end))
        else:
            # split equally to minimize padding
            num_chunks = int(np.ceil(duration / target_sec))
            chunk_len = duration / num_chunks

            for i in range(num_chunks):
                chunk_start = t_start + (i * chunk_len)
                chunk_end = chunk_start + chunk_len

                segments.append(TranscribedSegment(audio_path, chunk_start, chunk_end))

    return segments
