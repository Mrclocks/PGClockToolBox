from __future__ import annotations

import hmac
import secrets
from pathlib import Path

TOKEN_PATH = Path("/var/lib/pgclocktoolbox/data/admin_token")


def ensure_token() -> str:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TOKEN_PATH.exists():
        token = TOKEN_PATH.read_text(encoding="utf-8", errors="ignore").strip()
        if len(token) >= 32:
            return token
    token = secrets.token_urlsafe(48)
    TOKEN_PATH.write_text(token + "\n", encoding="utf-8")
    TOKEN_PATH.chmod(0o600)
    return token


def valid(token: str | None) -> bool:
    if not token or not TOKEN_PATH.exists():
        return False
    expected = TOKEN_PATH.read_text(encoding="utf-8", errors="ignore").strip()
    return bool(expected) and hmac.compare_digest(token, expected)
