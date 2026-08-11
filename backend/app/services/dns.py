from __future__ import annotations

import ipaddress
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

BACKUP = Path("/var/lib/pgclocktoolbox/data/resolv.conf.backup")
RESOLV_CONF = Path("/etc/resolv.conf")


@dataclass(slots=True)
class DnsStatus:
    method: str
    servers: list[str]
    resolv_conf: str
    managed: bool


def _run(args: list[str], timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def _valid_servers(servers: list[str]) -> list[str]:
    if not servers or len(servers) > 4:
        raise ValueError("Provide between 1 and 4 DNS servers")
    result: list[str] = []
    for value in servers:
        try:
            ip = ipaddress.ip_address(value.strip())
        except ValueError as exc:
            raise ValueError(f"Invalid DNS server: {value}") from exc
        if ip.is_unspecified or ip.is_multicast:
            raise ValueError(f"Invalid DNS server: {value}")
        result.append(str(ip))
    return result


def _resolv_conf_servers() -> list[str]:
    if not RESOLV_CONF.exists():
        return []
    values: list[str] = []
    try:
        text = RESOLV_CONF.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("nameserver "):
            value = line.split(None, 1)[1].strip()
            if value not in values:
                values.append(value)
    return values


def _default_interface() -> str | None:
    if not shutil.which("ip"):
        return None
    result = _run(["ip", "-o", "route", "show", "default"])
    for line in result.stdout.splitlines():
        parts = line.split()
        if "dev" in parts:
            idx = parts.index("dev")
            if idx + 1 < len(parts):
                return parts[idx + 1]
    return None


def _resolved_servers() -> list[str]:
    result = _run(["resolvectl", "status"])
    if result.returncode != 0:
        return []
    servers: list[str] = []
    for line in result.stdout.splitlines():
        if "DNS Servers:" in line:
            tail = line.split(":", 1)[1]
            for value in tail.split():
                if value not in servers:
                    servers.append(value)
    return servers


def status() -> DnsStatus:
    if shutil.which("resolvectl") and _resolved_servers():
        return DnsStatus("systemd-resolved", _resolved_servers(), str(RESOLV_CONF), BACKUP.exists())
    return DnsStatus("resolv.conf", _resolv_conf_servers(), str(RESOLV_CONF), BACKUP.exists())


def _backup_once() -> None:
    if not RESOLV_CONF.exists():
        raise RuntimeError("/etc/resolv.conf does not exist")
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        BACKUP.write_bytes(RESOLV_CONF.read_bytes())


def apply(servers: list[str]) -> DnsStatus:
    values = _valid_servers(servers)
    _backup_once()

    if shutil.which("resolvectl"):
        interface = _default_interface()
        if interface:
            result = _run(["resolvectl", "dns", interface, *values])
            if result.returncode == 0:
                _run(["resolvectl", "flush-caches"])
                return status()

    if RESOLV_CONF.is_symlink():
        raise RuntimeError("/etc/resolv.conf is managed by another resolver; configure that manager instead")
    try:
        lines = ["# Managed by PGClockToolBox", *[f"nameserver {value}" for value in values], ""]
        RESOLV_CONF.write_text("\n".join(lines), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"unable to update DNS: {exc}") from exc
    return status()


def restore() -> DnsStatus:
    if not BACKUP.exists():
        raise RuntimeError("No DNS backup is available")
    if RESOLV_CONF.is_symlink():
        raise RuntimeError("/etc/resolv.conf is managed by another resolver; restore through that manager")
    try:
        RESOLV_CONF.write_bytes(BACKUP.read_bytes())
    except OSError as exc:
        raise RuntimeError(f"unable to restore DNS: {exc}") from exc
    return status()


def status_dict(value: DnsStatus | None = None) -> dict[str, object]:
    return asdict(value or status())
