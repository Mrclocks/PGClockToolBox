from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

from app.core.paths import PASARGUARD_DATA, PASARGUARD_ENV, PASARGUARD_ROOT, TOOLBOX_BACKUPS
from app.services.backup.detector import detect_database
from app.services.backup.integrity import sha256_file
from app.services.backup.manifest import BackupManifest


@dataclass(slots=True)
class BackupResult:
    ok: bool
    path: str | None
    size: int
    checksum: str | None
    engine: str | None
    error: str | None = None


def _env_map() -> dict[str, str]:
    values: dict[str, str] = {}
    if not PASARGUARD_ENV.exists():
        return values
    for raw in PASARGUARD_ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def _run(command: list[str], env: dict[str, str] | None = None, stdin: bytes | None = None, timeout: int = 900) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, input=stdin, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def _database_dump(engine: str, destination: Path) -> None:
    env = _env_map()
    url = env.get("SQLALCHEMY_DATABASE_URL", "")
    parsed = urlparse(url)
    if engine == "sqlite":
        candidates = [PASARGUARD_DATA / "db.sqlite3", PASARGUARD_DATA / "pasarguard.db"]
        source = next((p for p in candidates if p.exists()), None)
        if source is None:
            raise RuntimeError("PasarGuard SQLite database was not found")
        # SQLite online backup is safer than a raw copy while the application is active.
        src = sqlite3.connect(str(source), uri=False)
        try:
            dst = sqlite3.connect(str(destination))
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        return

    if parsed.hostname is None:
        raise RuntimeError("SQLALCHEMY_DATABASE_URL has no database host")
    database = (parsed.path or "/").lstrip("/")
    user = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    host = parsed.hostname
    port = str(parsed.port or (3306 if engine in {"mysql", "mariadb"} else 5432))

    if engine in {"postgresql", "timescaledb"}:
        output = destination
        cmd = ["pg_dump", "--no-owner", "--no-privileges", "--format=custom", "--file", str(output), "--host", host, "--port", port, "--username", user, database]
        run_env = os.environ.copy()
        run_env["PGPASSWORD"] = password
        result = _run(cmd, env=run_env)
    else:
        output = destination
        cmd = ["mysqldump", "--single-transaction", "--routines", "--triggers", "--host", host, "--port", port, "--user", user, database]
        run_env = os.environ.copy()
        run_env["MYSQL_PWD"] = password
        result = _run(cmd, env=run_env)
        if result.ok:
            output.write_bytes(result.stdout)

    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "ignore")[-2500:]
        raise RuntimeError(f"database dump failed: {detail}")


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst, follow_symlinks=False)


def _zip_dir(root: Path, archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(root).as_posix())


def _validate_archive(archive: Path) -> None:
    with zipfile.ZipFile(archive, "r") as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"backup archive integrity check failed at {bad}")
        names = set(zf.namelist())
        if "pgclock/manifest.json" not in names:
            raise RuntimeError("backup manifest is missing")
        manifest = json.loads(zf.read("pgclock/manifest.json"))
        engine = manifest.get("db_engine")
        if engine == "sqlite" and not any(n.endswith("db.sqlite3") for n in names):
            raise RuntimeError("SQLite backup database is missing")
        if engine in {"postgresql", "timescaledb"} and "database/db.dump" not in names:
            raise RuntimeError("PostgreSQL backup dump is missing")
        if engine in {"mysql", "mariadb"} and "database/db.sql" not in names:
            raise RuntimeError("MySQL/MariaDB backup dump is missing")


def create_full_backup() -> BackupResult:
    TOOLBOX_BACKUPS.mkdir(parents=True, exist_ok=True)
    engine = detect_database().get("engine")
    if not engine:
        return BackupResult(False, None, 0, None, None, "Unable to detect PasarGuard database")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive = TOOLBOX_BACKUPS / f"pasarguard-full-{stamp}.zip"
    try:
        with tempfile.TemporaryDirectory(prefix="pgclock-backup-") as td:
            root = Path(td)
            (root / "pgclock").mkdir()
            (root / "database").mkdir()
            (root / "pasarguard").mkdir()

            if engine == "sqlite":
                _database_dump(engine, root / "database" / "db.sqlite3")
            elif engine in {"postgresql", "timescaledb"}:
                _database_dump(engine, root / "database" / "db.dump")
            else:
                _database_dump(engine, root / "database" / "db.sql")

            # Keep the restore-critical PasarGuard state. Secrets are intentionally included
            # in a full backup because PGClockMG needs the deployment environment to restore.
            _copy_tree(PASARGUARD_ROOT / ".env", root / "pasarguard" / ".env")
            for name in ("docker-compose.yml", "compose.yml", "docker-compose.yaml", "compose.yaml"):
                _copy_tree(PASARGUARD_ROOT / name, root / "pasarguard" / name)
            _copy_tree(PASARGUARD_DATA, root / "pasarguard" / "data")

            manifest = BackupManifest.create(db_engine=engine)
            manifest_path = root / "pgclock" / "manifest.json"
            manifest_path.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            _zip_dir(root, archive)

        _validate_archive(archive)
        checksum = sha256_file(archive)
        return BackupResult(True, str(archive), archive.stat().st_size, checksum, engine)
    except Exception as exc:
        try:
            archive.unlink(missing_ok=True)
        except OSError:
            pass
        return BackupResult(False, None, 0, None, engine, str(exc))


def backup_result_dict(result: BackupResult) -> dict[str, object]:
    return asdict(result)
