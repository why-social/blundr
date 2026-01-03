# Original Author: Maxine Orlen
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT

from io import StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import UploadFile


async def from_csv_or_str(
    file: Optional[UploadFile],
    _str: Optional[str],
) -> pd.DataFrame:
    """
    Accepts a csv as a file or string.
    If both are provided, prefers the string.
    Validates and returns a DataFrame. Raises ValueError on failure.
    """
    if not file and not _str:
        raise ValueError("Missing manifest. Provide a csv file or string.")

    csv_content = ""

    if _str:
        csv_content = _str
    elif file:
        if file.filename and not file.filename.lower().endswith(".csv"):
            raise ValueError(
                f"Invalid file type: '{file.filename}'. Must be a .csv file."
            )

        content_bytes = await file.read()
        await file.seek(0)

        try:
            csv_content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Invalid file encoding. Expected UTF-8.")

    try:
        if not csv_content.strip():
            raise ValueError("CSV content is empty.")

        df = pd.read_csv(StringIO(csv_content))

        if df.empty:
            raise ValueError("Parsed CSV contains no data rows.")

        return df

    except pd.errors.ParserError:
        raise ValueError("Content could not be parsed as a CSV.")
    except pd.errors.EmptyDataError:
        raise ValueError("CSV content is empty or malformed.")
    except Exception as e:
        raise ValueError(f"Error processing CSV: {str(e)}")


def process_batch_manifest(batch_dir: Path):
    manifest_path = batch_dir / "manifest.csv"
    if not manifest_path.exists():
        print(f"Warning: Skipping {batch_dir}, no manifest.csv found.")
        return None

    return pd.read_csv(manifest_path)


def clean_nones(value):
    """
    Recursively remove all None values from dictionaries and lists,
    and convert K8s objects to dicts.
    """
    if hasattr(value, "to_dict"):
        value = value.to_dict()

    if isinstance(value, list):
        return [clean_nones(x) for x in value if x is not None]
    elif isinstance(value, dict):
        return {key: clean_nones(val) for key, val in value.items() if val is not None}
    else:
        return value
