import csv
import io
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class Prediction:
    start_time: float
    end_time: float
    label: str = "unknown"
    confidence: float = 0.0

def predictions_to_csv(predictions: List[Prediction]) -> str:
    output = io.StringIO()

    fieldnames = ['start_time', 'end_time', 'label', 'confidence']

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')

    writer.writeheader()
    for pred in predictions:
        writer.writerow(asdict(pred))

    return output.getvalue()

