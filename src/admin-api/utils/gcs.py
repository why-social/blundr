from pathlib import Path
import os
import re

# TODO: write latest version as metadata in bucket root to avoid scanning directories
def get_latest_model_version(root: Path) -> int:
    """
    Scans the provided root path containing versioned directories in format v(d+).
    Returns the latest version.
    May raise FileNotFoundError and PermissionError
    """
    latest = 0
    version_pattern = re.compile(r'^v(\d+)$')

    # os.scandir is a generator that yields DirEntry objects.
    # This is more efficient than os.listdir() for GCS FUSE because 
    # it avoids extra 'stat' calls to check if an entry is a directory.
    with os.scandir(root) as entries:
        for entry in entries:
            if entry.is_dir():
                match = version_pattern.match(entry.name)
                if match:
                    latest = max(latest, int(match.group(1)))


    return latest
