from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

SYSCTL_BACKUP = Path("/var/lib/pgclocktoolbox/data/sysctl.backup")

# Conservative defaults for a VPN/proxy server. rp_filter is intentionally not
# changed globally because asymmetric VPN/WARP routes can legitimately require it.
RECOMMENDED = {
    "net.core.default_qdisc": "fq",
    "net.ipv4.tcp_congestion_control": "bbr",
    "net.ipv4.tcp_fastopen": "3",
    "net.ipv4.tcp_mtu_probing": "1",
    "net.ipv4.tcp_syncookies": "1",
}


@dataclass(slots=True)
class OptimizerStatus:
    kernel: str
    bbr_available: bool
    bbr_active: bool
    qdisc: str | None
    tcp_fastopen: str | None


def _run(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def status() -> OptimizerStatus:
    cc = _run(["sysctl", "-n", "net.ipv4.tcp_congestion_control"])
    qdisc = _run(["sysctl", "-n", "net.core.default_qdisc"])
    fastopen = _run(["sysctl", "-n", "net.ipv4.tcp_fastopen"])
    mod = _run(["modprobe", "-n", "bbr"])
    active = cc.returncode == 0 and cc.stdout.strip() == "bbr"
    return OptimizerStatus(platform.release(), mod.returncode == 0, active, qdisc.stdout.strip() if qdisc.returncode == 0 else None, fastopen.stdout.strip() if fastopen.returncode == 0 else None)


def _write_backup() -> None:
    SYSCTL_BACKUP.parent.mkdir(parents=True, exist_ok=True)
    current = _run(["sysctl", "-a"], timeout=20)
    if current.returncode != 0:
        raise RuntimeError(current.stderr.strip() or "unable to read current sysctl state")
    SYSCTL_BACKUP.write_text(current.stdout, encoding="utf-8")


def apply() -> OptimizerStatus:
    if not shutil.which("sysctl"):
        raise RuntimeError("sysctl is required")
    before = status()
    if not before.bbr_available:
        raise RuntimeError("BBR is not available in the running kernel")
    _write_backup()
    changed: list[str] = []
    try:
        for key, value in RECOMMENDED.items():
            result = _run(["sysctl", "-w", f"{key}={value}"])
            if result.returncode != 0:
                raise RuntimeError(f"failed to set {key}: {result.stderr.strip()}")
            changed.append(key)
        after = status()
        if not after.bbr_active or after.qdisc != "fq":
            raise RuntimeError("kernel accepted settings but verification failed")
        return after
    except Exception:
        for key in reversed(changed):
            _run(["sysctl", "-w", f"{key}={_read_backup_value(key)}"])
        raise


def _read_backup_value(key: str) -> str:
    if not SYSCTL_BACKUP.exists():
        return "0"
    prefix = f"{key} = "
    for line in SYSCTL_BACKUP.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return "0"
