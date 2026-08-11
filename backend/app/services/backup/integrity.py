from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def validate_archive_path(path: Path) -> tuple[bool, str]:
    if not path.exists() or not path.is_file():
        return False, "backup archive does not exist"
    if path.stat().st_size == 0:
        return False, "backup archive is empty"
    return True, "ok"
