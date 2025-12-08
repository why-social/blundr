from dataclasses import dataclass


@dataclass
class TranscribedSegment:
    sentence_idx: int
    start_time: float
    end_time: float
    label: str = "unknown"

    @property
    def duration(self):
        return self.end_time - self.start_time
