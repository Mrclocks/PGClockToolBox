from __future__ import annotations

import shutil
import subprocess
from typing import Any

from app.services.health.monitor import snapshot
from app.services.safety import audit

SAFE_SERVICES = {"pasarguard", "xray", "docker", "wg-quick"}


def _run(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def _service_exists(name: str) -> bool:
    return _run(["systemctl", "cat", name], 5).returncode == 0


def heal() -> dict[str, Any]:
    before = snapshot()
    actions: list[str] = []
    # Only restart a service when it is known to exist and is explicitly unhealthy.
    # Never touch networking, firewall, routing or DNS automatically from this layer.
    checks = (("pasarguard", "pasarguard"), ("xray", "xray"), ("docker", "docker"))
    for label, unit in checks:
        if not _service_exists(unit):
            continue
        status = _run(["systemctl", "is-active", unit], 5)
        if status.stdout.strip() == "active":
            continue
        result = _run(["systemctl", "restart", unit], 45)
        if result.returncode == 0:
            actions.append(f"restarted:{unit}")
            audit("auto_heal", "success", {"service": unit})
        else:
            audit("auto_heal", "failed", {"service": unit, "error": (result.stderr or result.stdout)[-1000:]})
    after = snapshot()
    return {"before": before, "after": after, "actions": actions}
