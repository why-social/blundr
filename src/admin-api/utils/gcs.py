import hashlib
import os
import re
from pathlib import Path
from typing import Dict

from fastapi.concurrency import run_in_threadpool

from consts import CAS_DIR_NAME, MODELS_MOUNT_ROOT

_created_dirs_cache = set()


# TODO: write latest version as metadata in bucket root to avoid scanning directories
def get_latest_model_version() -> int:
    """
    Scans the provided root path containing versioned directories in format v(d+).
    Returns the latest version.
    May raise FileNotFoundError and PermissionError
    """
    latest = 0
    version_pattern = re.compile(r"^v(\d+)$")

    # os.scandir is a generator that yields DirEntry objects.
    # This is more efficient than os.listdir() for GCS FUSE because
    # it avoids extra 'stat' calls to check if an entry is a directory.
    with os.scandir(MODELS_MOUNT_ROOT) as entries:
        for entry in entries:
            if entry.is_dir():
                match = version_pattern.match(entry.name)
                if match:
                    latest = max(latest, int(match.group(1)))

    return latest


def _check_fs_blocking(
    root: Path, file_hash: str, filename: str, content: bytes
) -> Dict:
    """
    Blocking I/O operations (mkdir, exists) to be run in a threadpool.
    """
    # format: <root>/e5/3a/e53a22... .jpg
    shard_relative = Path(file_hash[:2]) / file_hash[2:4]
    shard_absolute = root / shard_relative
    if str(shard_absolute) not in _created_dirs_cache:
        shard_absolute.mkdir(parents=True, exist_ok=True)
        _created_dirs_cache.add(str(shard_absolute))

    final_name = f"{file_hash}{Path(filename).suffix}"
    abs_path = shard_absolute / final_name
    rel_path = Path(CAS_DIR_NAME) / shard_relative / final_name

    if not abs_path.exists():
        with open(abs_path, "wb") as f:
            f.write(content)

    return {
        "exists": abs_path.exists(),
        "path": str(rel_path),
        "hash": file_hash,
    }


async def save_to_cas(root: Path, content: bytes, original_filename: str) -> Dict:
    """
    Hashes content and saves to global CAS store if not exists.
    Returns dict with hash, path, and is_new status.
    """
    sha256 = hashlib.sha256(content)
    file_hash = sha256.hexdigest()

    fs_result = await run_in_threadpool(
        _check_fs_blocking, root, file_hash, original_filename, content
    )

    return fs_result
