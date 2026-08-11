from __future__ import annotations

import shutil
import socket
import subprocess
from pathlib import Path

from app.core.paths import PASARGUARD_ROOT


def _cmd(args: list[str], timeout: int = 4) -> tuple[bool, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return p.returncode == 0, (p.stdout or p.stderr).strip()[-1000:]
    except (OSError, subprocess.SubprocessError):
        return False, "command unavailable"


def snapshot() -> dict[str, object]:
    disk = shutil.disk_usage("/")
    load = Path("/proc/loadavg").read_text(encoding="utf-8").split()[:3] if Path("/proc/loadavg").exists() else []
    memory = {}
    if Path("/proc/meminfo").exists():
        for line in Path("/proc/meminfo").read_text().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                memory[k] = v.strip()
    xray = shutil.which("xray")
    wg = shutil.which("wg")
    pasarguard = PASARGUARD_ROOT.exists()
    dns_ok, _ = _cmd(["resolvectl", "status"], 3) if shutil.which("resolvectl") else (True, "not-managed")
    internet = False
    try:
        with socket.create_connection(("1.1.1.1", 443), timeout=3):
            internet = True
    except OSError:
        pass
    return {
        "status": "ok" if pasarguard and internet else "degraded",
        "pasarguard": pasarguard,
        "xray": bool(xray),
        "wireguard": bool(wg),
        "dns": dns_ok,
        "internet": internet,
        "disk": {"total": disk.total, "used": disk.used, "free": disk.free, "percent": round(disk.used / disk.total * 100, 1)},
        "load": load,
        "memory": memory,
    }
