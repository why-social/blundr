from dataclasses import dataclass
from pathlib import Path


@dataclass
class TranscribedSegment:
    audio_path: Path
    start_time: float
    end_time: float
    label: str = "unknown"

    @property
    def duration(self):
        return self.end_time - self.start_time
