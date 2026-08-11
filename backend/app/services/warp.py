from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from app.services.safety import audit


@dataclass(slots=True)
class WarpStatus:
    installed: bool
    version: str | None
    connected: bool | None
    registered: bool | None = None
    protocol: str | None = None
    raw: str = ""


def _run(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def status() -> WarpStatus:
    if not shutil.which("warp-cli"):
        return WarpStatus(False, None, None, False)
    v = _run(["warp-cli", "--version"])
    s = _run(["warp-cli", "status"])
    low = s.stdout.lower()
    registered = "registration" in low and "not registered" not in low
    protocol = None
    for line in s.stdout.splitlines():
        if "protocol" in line.lower() and ":" in line:
            protocol = line.split(":", 1)[1].strip()
    return WarpStatus(True, (v.stdout or v.stderr).strip() or None, "connected" in low, registered, protocol, (s.stdout or s.stderr).strip())


def install() -> None:
    if shutil.which("warp-cli"):
        return
    if not shutil.which("apt-get"):
        raise RuntimeError("WARP installation requires an apt-based Ubuntu system")
    update = _run(["apt-get", "update"], timeout=180)
    if update.returncode != 0:
        raise RuntimeError((update.stderr or update.stdout).strip()[-1600:])
    result = _run(["apt-get", "install", "-y", "cloudflare-warp"], timeout=300)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1600:])
    audit("warp_install", "success")


def register() -> None:
    if not shutil.which("warp-cli"):
        raise RuntimeError("WARP is not installed")
    current = status()
    if current.registered:
        return
    result = _run(["warp-cli", "registration", "new"], timeout=60)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1600:])
    audit("warp_register", "success")


def connect() -> None:
    if not shutil.which("warp-cli"):
        raise RuntimeError("WARP is not installed")
    register()
    mode = _run(["warp-cli", "mode", "warp+doh"])
    if mode.returncode != 0:
        raise RuntimeError((mode.stderr or mode.stdout).strip()[-1200:])
    # MASQUE is the current default protocol for new Linux WARP profiles.
    protocol = _run(["warp-cli", "tunnel", "protocol", "set", "MASQUE"])
    if protocol.returncode != 0:
        # Older clients may not expose protocol selection; connection can still proceed.
        audit("warp_protocol", "skipped", {"error": (protocol.stderr or protocol.stdout).strip()[-600:]})
    result = _run(["warp-cli", "connect"], timeout=60)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1200:])
    audit("warp_connect", "success")


def disconnect() -> None:
    result = _run(["warp-cli", "disconnect"], timeout=30)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1200:])
    audit("warp_disconnect", "success")


def add_host(host: str) -> None:
    _validate_host(host)
    result = _run(["warp-cli", "tunnel", "host", "add", host])
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1200:])


def remove_host(host: str) -> None:
    _validate_host(host)
    result = _run(["warp-cli", "tunnel", "host", "remove", host])
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1200:])


def add_ip(cidr: str) -> None:
    if len(cidr) > 64 or any(c in cidr for c in ";&|`$\n"):
        raise ValueError("invalid IP/CIDR")
    result = _run(["warp-cli", "tunnel", "ip", "add", cidr])
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1200:])


def remove_ip(cidr: str) -> None:
    if len(cidr) > 64 or any(c in cidr for c in ";&|`$\n"):
        raise ValueError("invalid IP/CIDR")
    result = _run(["warp-cli", "tunnel", "ip", "remove", cidr])
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1200:])


def _validate_host(host: str) -> None:
    if len(host) > 253 or not host or any(c in host for c in ";&|`$\n "):
        raise ValueError("invalid hostname")
