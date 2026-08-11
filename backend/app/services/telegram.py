from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.paths import TOOLBOX_DATA

CONFIG = TOOLBOX_DATA / "telegram.env"
TELEGRAM_DOCUMENT_LIMIT = 49 * 1024 * 1024


def _safe(value: str, max_len: int = 4096) -> str:
    value = value.strip()
    if not value or len(value) > max_len or any(c in value for c in "\r\n\x00"):
        raise ValueError("invalid Telegram configuration")
    return value


def _stored() -> tuple[str | None, str | None, str | None]:
    values: dict[str, str] = {}
    try:
        for line in CONFIG.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    except OSError:
        pass
    return values.get("PGCLOCK_TELEGRAM_BOT_TOKEN"), values.get("PGCLOCK_TELEGRAM_CHAT_ID"), values.get("PGCLOCK_TELEGRAM_PROXY") or None


def send_document(path: Path, token: str, chat_id: str, proxy: str | None = None, caption: str | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    token = _safe(token)
    chat_id = _safe(chat_id, 256)
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    cmd = ["curl", "--fail", "--silent", "--show-error", "--connect-timeout", "15", "--max-time", "900"]
    if proxy:
        cmd += ["--proxy", _safe(proxy, 2048)]
    cmd += ["-F", f"chat_id={chat_id}", "-F", f"document=@{path}"]
    if caption:
        cmd += ["-F", f"caption={caption[:900]}"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=920, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-2000:])


def send_backup(path: Path, token: str, chat_id: str, proxy: str | None = None, caption: str | None = None) -> int:
    """Send a backup as one document or deterministic chunks under Telegram's Bot API limit."""
    if path.stat().st_size <= TELEGRAM_DOCUMENT_LIMIT:
        send_document(path, token, chat_id, proxy, caption)
        return 1
    count = 0
    with tempfile.TemporaryDirectory(prefix="pgclock-tg-") as td:
        chunk_dir = Path(td)
        with path.open("rb") as source:
            index = 1
            while True:
                data = source.read(TELEGRAM_DOCUMENT_LIMIT)
                if not data:
                    break
                chunk = chunk_dir / f"{path.name}.part{index:03d}"
                chunk.write_bytes(data)
                send_document(chunk, token, chat_id, proxy, f"{caption or 'PGClockToolBox backup'} · part {index}")
                count += 1
                index += 1
    return count


def config_from_env() -> tuple[str | None, str | None, str | None]:
    stored = _stored()
    return (os.getenv("PGCLOCK_TELEGRAM_BOT_TOKEN") or stored[0], os.getenv("PGCLOCK_TELEGRAM_CHAT_ID") or stored[1], os.getenv("PGCLOCK_TELEGRAM_PROXY") or stored[2])
