from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from app.core.paths import PASARGUARD_DATA, PASARGUARD_ENV, PASARGUARD_ROOT
from app.services.discovery import run_readonly

_VERSION_RE = re.compile(r"(?:version|v)[^0-9]*([0-9]+(?:\.[0-9]+){1,3})", re.I)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _version_from_command(command: list[str]) -> str | None:
    result = run_readonly(command, timeout=3)
    text = f"{result.stdout}\n{result.stderr}"
    match = _VERSION_RE.search(text)
    return match.group(1) if match else (result.stdout.strip() or None)


def _docker_service(name: str) -> dict[str, Any]:
    result = run_readonly(["docker", "inspect", "--format", "{{json .State}}", name], timeout=3)
    if not result.ok or not result.stdout:
        return {"name": name, "exists": False}
    try:
        state = json.loads(result.stdout)
    except json.JSONDecodeError:
        state = {"raw": result.stdout}
    return {"name": name, "exists": True, "running": bool(state.get("Running")), "status": state.get("Status"), "health": (state.get("Health") or {}).get("Status")}


def discover_installation() -> dict[str, Any]:
    """Read-only, installation-aware inventory. No configuration is changed."""
    env = _read_text(PASARGUARD_ENV)
    compose = PASARGUARD_ROOT / "docker-compose.yml"
    compose_alt = PASARGUARD_ROOT / "compose.yml"
    xray_paths = [PASARGUARD_ROOT / "xray", PASARGUARD_DATA / "xray", Path("/etc/xray"), Path("/usr/local/etc/xray")]
    xray_config_paths = [p for p in xray_paths if p.exists()]

    wg = run_readonly(["wg", "show", "all", "dump"], timeout=4)
    wg_interfaces: list[str] = []
    if wg.ok:
        for line in wg.stdout.splitlines():
            if line and not line.startswith("interface"):
                wg_interfaces.append(line.split("\t", 1)[0])

    docker_services: list[dict[str, Any]] = []
    if run_readonly(["docker", "version", "--format", "{{.Server.Version}}"], timeout=3).ok:
        ps = run_readonly(["docker", "ps", "--format", "{{.Names}}"], timeout=4)
        if ps.ok:
            docker_services = [_docker_service(name) for name in ps.stdout.splitlines() if name]

    xray_bin = shutil.which("xray")
    return {
        "pasarguard": {
            "installed": PASARGUARD_ROOT.is_dir() and PASARGUARD_ENV.is_file(),
            "root": str(PASARGUARD_ROOT), "data": str(PASARGUARD_DATA), "env": str(PASARGUARD_ENV),
            "compose_file": str(compose if compose.exists() else compose_alt) if (compose.exists() or compose_alt.exists()) else None,
            "env_has_database_url": "SQLALCHEMY_DATABASE_URL=" in env,
        },
        "xray": {"binary": xray_bin, "version": _version_from_command(["xray", "version"]) if xray_bin else None, "known_config_paths": [str(p) for p in xray_config_paths]},
        "wireguard": {"wg_binary": shutil.which("wg"), "wg_quick": shutil.which("wg-quick"), "interfaces": sorted(set(wg_interfaces)), "kernel_module": run_readonly(["modprobe", "-n", "wireguard"], timeout=3).ok},
        "docker": {"services": docker_services},
        "database": {"sqlite_file": str(PASARGUARD_DATA / "db.sqlite3") if (PASARGUARD_DATA / "db.sqlite3").exists() else None, "env_database_url_present": "SQLALCHEMY_DATABASE_URL=" in env},
    }
