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
    for line in RESOLV_CONF.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("nameserver "):
            value = line.split(None, 1)[1].strip()
            if value not in values:
                values.append(value)
    return values


def status() -> DnsStatus:
    if shutil.which("resolvectl"):
        result = _run(["resolvectl", "status"])
        servers: list[str] = []
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "DNS Servers:" in line:
                    tail = line.split(":", 1)[1]
                    servers.extend(x for x in tail.split() if x not in servers)
        if servers:
            return DnsStatus("systemd-resolved", servers, str(RESOLV_CONF), BACKUP.exists())
    return DnsStatus("resolv.conf", _resolv_conf_servers(), str(RESOLV_CONF), BACKUP.exists())


def apply(servers: list[str]) -> DnsStatus:
    values = _valid_servers(servers)
    if not RESOLV_CONF.exists():
        raise RuntimeError("/etc/resolv.conf does not exist")
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        BACKUP.write_bytes(RESOLV_CONF.read_bytes())

    if shutil.which("resolvectl"):
        result = _run(["resolvectl", "dns", "--interface", "", *values])
        if result.returncode == 0:
            return status()

    try:
        lines = ["# Managed by PGClockToolBox", *[f"nameserver {value}" for value in values], ""]
        RESOLV_CONF.write_text("\n".join(lines), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"unable to update DNS: {exc}") from exc
    return status()


def restore() -> DnsStatus:
    if not BACKUP.exists():
        raise RuntimeError("No DNS backup is available")
    try:
        RESOLV_CONF.write_bytes(BACKUP.read_bytes())
    except OSError as exc:
        raise RuntimeError(f"unable to restore DNS: {exc}") from exc
    return status()


def status_dict(value: DnsStatus | None = None) -> dict[str, object]:
    return asdict(value or status())
