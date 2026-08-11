from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

CANDIDATE_ROOTS = [Path("/opt"), Path("/etc"), Path("/var/lib")]
KEYWORDS = ("pg-node", "pasarguard-node", "pasarguard_node", "pasarguardnode")
NODE_SERVICE_RE = re.compile(r"^(?:pg-node|node-[a-zA-Z0-9_.-]+)(?:\.service)?$")


def _run(args: list[str], timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def discover_local_nodes() -> list[dict[str, object]]:
    found: dict[str, dict[str, object]] = {}

    # Official one-click installations can create a named service such as node-eu-1.
    if shutil.which("systemctl"):
        units = _run(["systemctl", "list-unit-files", "--type=service", "--no-legend", "--no-pager"], 8)
        if units.returncode == 0:
            for line in units.stdout.splitlines():
                name = line.split(None, 1)[0] if line.split() else ""
                if not NODE_SERVICE_RE.fullmatch(name):
                    continue
                unit = name.removesuffix(".service")
                state = _run(["systemctl", "is-active", name], 4).stdout.strip()
                found[unit] = {"name": unit, "service": name, "status": state or "unknown", "source": "systemd"}

    if shutil.which("docker"):
        ps = _run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}"], 8)
        if ps.returncode == 0:
            for line in ps.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) != 3:
                    continue
                name, image, status = parts
                low = f"{name} {image}".lower()
                if any(k in low for k in KEYWORDS) or "pasarguard/node" in low:
                    found[name] = {"name": name, "image": image, "status": status, "source": "docker"}

    for base in CANDIDATE_ROOTS:
        if not base.exists():
            continue
        try:
            entries = list(base.iterdir())
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir() or not any(k in entry.name.lower() for k in KEYWORDS):
                continue
            found.setdefault(entry.name, {"name": entry.name, "path": str(entry), "source": "filesystem"})

    return sorted(found.values(), key=lambda item: str(item.get("name", "")))
