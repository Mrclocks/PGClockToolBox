from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _safe(value: str, max_len: int = 4096) -> str:
    value = value.strip()
    if not value or len(value) > max_len or any(c in value for c in "\r\n\x00"):
        raise ValueError("invalid Telegram configuration")
    return value


def send_document(path: Path, token: str, chat_id: str, proxy: str | None = None, caption: str | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    token = _safe(token)
    chat_id = _safe(chat_id, 256)
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    cmd = ["curl", "--fail", "--silent", "--show-error", "--connect-timeout", "15", "--max-time", "900"]
    if proxy:
        proxy = _safe(proxy, 2048)
        cmd += ["--proxy", proxy]
    cmd += ["-F", f"chat_id={chat_id}", "-F", f"document=@{path}"]
    if caption:
        cmd += ["-F", f"caption={caption[:900]}"]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=920, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-2000:])


def config_from_env() -> tuple[str | None, str | None, str | None]:
    return os.getenv("PGCLOCK_TELEGRAM_BOT_TOKEN"), os.getenv("PGCLOCK_TELEGRAM_CHAT_ID"), os.getenv("PGCLOCK_TELEGRAM_PROXY")
