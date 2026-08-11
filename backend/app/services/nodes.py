from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


CANDIDATE_ROOTS = [Path("/opt"), Path("/etc"), Path("/var/lib")]
KEYWORDS = ("pg-node", "pasarguard-node", "pasarguard_node")


def _run(args: list[str], timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def discover_local_nodes() -> list[dict[str, object]]:
    found: dict[str, dict[str, object]] = {}
    if shutil.which("docker"):
        ps = _run(["docker", "ps", "-a", "--format", "{{.Names}}\\t{{.Image}}\\t{{.Status}}"])
        if ps.returncode == 0:
            for line in ps.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) != 3:
                    continue
                name, image, status = parts
                low = f"{name} {image}".lower()
                if any(k in low for k in KEYWORDS):
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
