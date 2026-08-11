from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.paths import PASARGUARD_DATA, PASARGUARD_ENV, PASARGUARD_ROOT


@dataclass(slots=True)
class CommandResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


@dataclass(slots=True)
class ServerDiscovery:
    os_name: str
    os_version: str | None
    architecture: str
    kernel: str
    pasarguard_installed: bool
    pasarguard_root: str
    pasarguard_data: str
    xray_installed: bool
    wireguard_installed: bool
    docker_installed: bool
    docker_compose_installed: bool
    database_hint: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def run_readonly(command: list[str], timeout: float = 5.0) -> CommandResult:
    """Run a fixed read-only probe. Never accept shell strings from the web layer."""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            completed.returncode == 0,
            completed.stdout.strip(),
            completed.stderr.strip(),
            completed.returncode,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return CommandResult(False, stderr=str(exc), returncode=1)


def _ubuntu_version() -> str | None:
    path = Path("/etc/os-release")
    if not path.exists():
        return None
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values.get("VERSION_ID")


def _database_hint() -> str | None:
    if not PASARGUARD_ENV.exists():
        return None
    text = PASARGUARD_ENV.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        if line.startswith("SQLALCHEMY_DATABASE_URL="):
            value = line.split("=", 1)[1].strip().strip('"').lower()
            if "sqlite" in value:
                return "sqlite"
            if "timescale" in value:
                return "timescaledb"
            if "postgres" in value:
                return "postgresql"
            if "mariadb" in value:
                return "mariadb"
            if "mysql" in value:
                return "mysql"
    if (PASARGUARD_DATA / "db.sqlite3").exists():
        return "sqlite"
    return None


def discover() -> ServerDiscovery:
    return ServerDiscovery(
        os_name="linux",
        os_version=_ubuntu_version(),
        architecture=platform.machine(),
        kernel=platform.release(),
        pasarguard_installed=PASARGUARD_ROOT.exists() and PASARGUARD_ENV.exists(),
        pasarguard_root=str(PASARGUARD_ROOT),
        pasarguard_data=str(PASARGUARD_DATA),
        xray_installed=shutil.which("xray") is not None,
        wireguard_installed=shutil.which("wg") is not None,
        docker_installed=shutil.which("docker") is not None,
        docker_compose_installed=run_readonly(["docker", "compose", "version"]).ok,
        database_hint=_database_hint(),
    )
