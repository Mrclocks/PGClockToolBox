from pathlib import Path

PASARGUARD_ROOT = Path("/opt/pasarguard")
PASARGUARD_ENV = PASARGUARD_ROOT / ".env"
PASARGUARD_DATA = Path("/var/lib/pasarguard")
TOOLBOX_ROOT = Path("/var/lib/pgclocktoolbox")
TOOLBOX_DATA = TOOLBOX_ROOT / "data"
TOOLBOX_BACKUPS = TOOLBOX_ROOT / "backups"
TOOLBOX_LOGS = TOOLBOX_ROOT / "logs"
