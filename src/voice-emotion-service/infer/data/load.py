from io import StringIO
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from common.config.dataset_config import DatasetConfig
from data.segment import TranscribedSegment


def load_transcribed_segments(
    transcript: str, audio_path: Path, config: DatasetConfig
) -> List[TranscribedSegment]:
    """
    Reads CSV and splits speaking sections into chunks matching the maximum size
    from `DatasetConfig`, and optimising for minimal padding.
    """
    assert audio_path.exists(), f"ERROR: Audio file not found: {audio_path}"

    if not transcript:
        return []

    if "\\n" in transcript:
        transcript = transcript.replace("\\n", "\n")  # make newlines work

    transcript = transcript.replace("\r", "")  # fix windows strings
    transcript = transcript.strip()  # sanity check blank leading/trailing lines

    trans_buf = StringIO(transcript)
    df = pd.read_csv(trans_buf, skipinitialspace=True)
    print(f"INFO [load_transcribed_segments()]: loaded {df.size} transcription entries")
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
