from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class BackupManifest:
    format: str = "pgclock-pasarguard-backup"
    format_version: int = 1
    created_at: str = ""
    pasarguard_version: str | None = None
    db_engine: str | None = None
    backup_type: str = "full"
    scope: str = "panel_and_nodes"
    encrypted: bool = False
    compressed: bool = True
    node_count: int = 0
    checksum_algorithm: str = "sha256"

    @classmethod
    def create(cls, **kwargs: object) -> "BackupManifest":
        return cls(created_at=datetime.now(timezone.utc).isoformat(), **kwargs)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
