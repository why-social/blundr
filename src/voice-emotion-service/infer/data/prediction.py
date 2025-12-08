import csv
import io
from dataclasses import asdict, dataclass
from typing import List


@dataclass
class Prediction:
    start_time: float
    end_time: float
    label: str = "unknown"
    confidence: float = 0.0


def predictions_to_csv(predictions: List[Prediction]) -> str:
    output = io.StringIO()

    fieldnames = ["start_time", "end_time", "label", "confidence"]

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")

    writer.writeheader()
    for pred in predictions:
        row = asdict(pred)

        row["start_time"] = f"{pred.start_time:.2f}"
        row["end_time"] = f"{pred.end_time:.2f}"
        row["confidence"] = f"{pred.confidence:.2f}"

        writer.writerow(row)

    return output.getvalue()
