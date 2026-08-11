from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.paths import TOOLBOX_DATA

ROOT = TOOLBOX_DATA / "snapshots"
AUDIT = TOOLBOX_DATA / "audit.jsonl"


def audit(action: str, status: str, details: dict[str, Any] | None = None) -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "action": action, "status": status, "details": details or {}}, ensure_ascii=False) + "\n")
    AUDIT.chmod(0o600)


def snapshot_file(path: Path, label: str) -> Path | None:
    if not path.exists() or not path.is_file():
        return None
    ROOT.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in label)
    target = ROOT / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{safe}"
    shutil.copy2(path, target)
    target.chmod(0o600)
    return target


def recent_audit(limit: int = 100) -> list[dict[str, Any]]:
    if not AUDIT.exists():
        return []
    rows = AUDIT.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    result: list[dict[str, Any]] = []
    for row in rows:
        try:
            result.append(json.loads(row))
        except json.JSONDecodeError:
            continue
    return list(reversed(result))
