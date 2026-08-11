from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.paths import PASARGUARD_DATA, PASARGUARD_ROOT


@dataclass(frozen=True, slots=True)
class BackupPath:
    source: Path
    archive_name: str
    required: bool = False


def collection_plan() -> list[BackupPath]:
    """Return conservative paths; missing optional paths are skipped by the collector."""
    return [
        BackupPath(PASARGUARD_ROOT / ".env", "pasarguard/.env", required=True),
        BackupPath(PASARGUARD_ROOT / "docker-compose.yml", "pasarguard/docker-compose.yml"),
        BackupPath(PASARGUARD_ROOT / "compose.yml", "pasarguard/compose.yml"),
        BackupPath(PASARGUARD_DATA, "pasarguard/data"),
    ]
