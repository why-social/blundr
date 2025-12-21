from io import StringIO
from typing import Optional
from fastapi import UploadFile
import pandas as pd

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
             raise ValueError(f"Invalid file type: '{file.filename}'. Must be a .csv file.")

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

def validate_manifest_df(manifest_df: pd.DataFrame):
    """
    Validate manifest has a filename an a label columns
    """
