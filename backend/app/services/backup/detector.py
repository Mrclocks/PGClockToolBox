from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from app.core.paths import PASARGUARD_DATA, PASARGUARD_ENV


def detect_database() -> dict[str, str | None]:
    """Detect the PasarGuard DB family without exposing credentials."""
    if PASARGUARD_ENV.exists():
        for line in PASARGUARD_ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.startswith("SQLALCHEMY_DATABASE_URL="):
                continue
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            scheme = urlparse(value).scheme.lower()
            mapping = {
                "sqlite+aiosqlite": "sqlite", "sqlite": "sqlite",
                "postgresql+asyncpg": "postgresql", "postgresql": "postgresql",
                "mysql+asyncmy": "mysql", "mysql": "mysql",
                "mariadb+asyncmy": "mariadb", "mariadb": "mariadb",
            }
            engine = mapping.get(scheme)
            if engine:
                return {"engine": engine, "source": "env"}
    sqlite = PASARGUARD_DATA / "db.sqlite3"
    if sqlite.exists():
        return {"engine": "sqlite", "source": str(sqlite)}
    return {"engine": None, "source": None}
