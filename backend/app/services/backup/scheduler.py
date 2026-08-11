from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from app.core.paths import TOOLBOX_BACKUPS, TOOLBOX_DATA
from app.services.backup.engine import backup_result_dict, create_full_backup

CONFIG = TOOLBOX_DATA / "backup_schedule.json"
LOCK = threading.Lock()

@dataclass(slots=True)
class BackupSchedule:
    enabled: bool = False
    interval_hours: int = 24
    retention: int = 7
    next_run: str | None = None
    last_run: str | None = None
    last_status: str = "never"
    last_error: str | None = None


def load() -> BackupSchedule:
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
        return BackupSchedule(**{k: data[k] for k in BackupSchedule.__dataclass_fields__ if k in data})
    except (OSError, ValueError, TypeError):
        return BackupSchedule()


def save(value: BackupSchedule) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(value), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CONFIG)


def prune(retention: int) -> int:
    archives = sorted(TOOLBOX_BACKUPS.glob("pasarguard-full-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for path in archives[retention:]:
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def run_now(force: bool = False) -> dict[str, object]:
    if not LOCK.acquire(blocking=False):
        return {"status": "running"}
    try:
        value = load()
        now = datetime.now(timezone.utc)
        if not force and not value.enabled:
            return {"status": "disabled"}
        if not force and value.last_run:
            try:
                last = datetime.fromisoformat(value.last_run)
                if now < last + timedelta(hours=value.interval_hours):
                    value.next_run = (last + timedelta(hours=value.interval_hours)).isoformat()
                    save(value)
                    return {"status": "not_due", "next_run": value.next_run}
            except ValueError:
                pass
        value.last_run = now.isoformat()
        value.last_status = "running"
        value.last_error = None
        save(value)
        result = create_full_backup()
        value.last_status = "success" if result.ok else "failed"
        value.last_error = result.error
        value.next_run = (now + timedelta(hours=value.interval_hours)).isoformat()
        save(value)
        if result.ok:
            prune(value.retention)
        return {"status": value.last_status, **backup_result_dict(result), "next_run": value.next_run}
    finally:
        LOCK.release()


def configure(enabled: bool, interval_hours: int, retention: int) -> BackupSchedule:
    if interval_hours not in {1, 2, 3, 4, 6, 8, 12, 24, 48, 72}:
        raise ValueError("Unsupported backup interval")
    if retention < 1 or retention > 100:
        raise ValueError("Retention must be between 1 and 100")
    value = load()
    value.enabled = enabled
    value.interval_hours = interval_hours
    value.retention = retention
    value.next_run = (datetime.now(timezone.utc) + timedelta(hours=interval_hours)).isoformat() if enabled else None
    save(value)
    if enabled:
        prune(retention)
    return value
