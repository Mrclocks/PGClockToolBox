from __future__ import annotations

import json
import zipfile
from pathlib import Path

from app.services.backup.integrity import sha256_file
from app.services.backup.manifest import BackupManifest


def test_manifest_has_stable_format():
    manifest = BackupManifest.create(db_engine="sqlite", node_count=2)
    data = manifest.to_dict()
    assert data["format"] == "pgclock-pasarguard-backup"
    assert data["format_version"] == 1
    assert data["db_engine"] == "sqlite"
    assert data["node_count"] == 2
    json.dumps(data)


def test_sha256(tmp_path: Path):
    path = tmp_path / "x"
    path.write_bytes(b"pgclock")
    assert len(sha256_file(path)) == 64


def test_pgclockmg_compatible_shapes(tmp_path: Path):
    archive = tmp_path / "backup.zip"
    manifest = BackupManifest.create(db_engine="postgresql").to_dict()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(".env", "SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://example\n")
        zf.writestr("db_backup.sql", "-- pg_dump\n")
        zf.writestr("pgclock/manifest.json", json.dumps(manifest))
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
    assert ".env" in names
    assert "db_backup.sql" in names
    assert "pgclock/manifest.json" in names
