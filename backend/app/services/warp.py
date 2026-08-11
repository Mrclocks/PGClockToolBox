from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class WarpStatus:
    installed: bool
    version: str | None
    connected: bool | None
    raw: str = ""


def _run(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def status() -> WarpStatus:
    if not shutil.which("warp-cli"):
        return WarpStatus(False, None, None)
    v = _run(["warp-cli", "--version"])
    s = _run(["warp-cli", "status"])
    low = s.stdout.lower()
    return WarpStatus(True, (v.stdout or v.stderr).strip() or None, "connected" in low, (s.stdout or s.stderr).strip())


def connect() -> None:
    if not shutil.which("warp-cli"):
        raise RuntimeError("WARP is not installed")
    mode = _run(["warp-cli", "mode", "warp+doh"])
    if mode.returncode != 0:
        raise RuntimeError((mode.stderr or mode.stdout).strip()[-1200:])
    result = _run(["warp-cli", "connect"], timeout=60)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1200:])


def disconnect() -> None:
    result = _run(["warp-cli", "disconnect"], timeout=30)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-1200:])


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
