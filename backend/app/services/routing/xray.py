from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.core.paths import PASARGUARD_DATA, PASARGUARD_ROOT
from app.services.routing.engine import Rule, load
from app.services.safety import audit, snapshot_file

OUTBOUND_TAG = "pgclock-warp"
DIRECT_TAG = "pgclock-direct"


def _candidate_configs() -> list[Path]:
    paths = [
        PASARGUARD_DATA / "xray_config.json",
        PASARGUARD_DATA / "xray" / "config.json",
        PASARGUARD_ROOT / "xray_config.json",
        Path("/usr/local/etc/xray/config.json"),
        Path("/etc/xray/config.json"),
    ]
    return [p for p in paths if p.is_file()]


def locate_config() -> str | None:
    candidates = _candidate_configs()
    return str(candidates[0]) if candidates else None


def _rule_to_xray(rule: Rule) -> dict[str, Any]:
    item: dict[str, Any] = {"type": "field", "outboundTag": OUTBOUND_TAG if rule.action == "warp" else DIRECT_TAG}
    if rule.kind == "domain":
        item["domain"] = [rule.value]
    elif rule.kind in {"ip", "cidr", "geoip"}:
        item["ip"] = [rule.value if rule.kind != "geoip" else f"geoip:{rule.value}"]
    elif rule.kind == "geosite":
        item["domain"] = [f"geosite:{rule.value}"]
    elif rule.kind == "port":
        item["port"] = rule.value
    if rule.ports:
        item["port"] = ",".join(str(p) for p in rule.ports)
    if rule.protocol != "tcp,udp":
        item["network"] = rule.protocol
    return item


def preview() -> dict[str, Any]:
    path = locate_config()
    rules = load()
    return {"config": path, "rules": [_rule_to_xray(r) for r in rules], "can_apply": bool(path)}


def validate_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "error": "Xray configuration not found"}
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)}
    if not isinstance(config.get("inbounds"), list) or not isinstance(config.get("outbounds"), list):
        return {"ok": False, "error": "Xray config must contain inbounds and outbounds arrays"}
    tags = [o.get("tag") for o in config["outbounds"] if isinstance(o, dict)]
    if len(tags) != len(set(tags)):
        return {"ok": False, "error": "Xray outbound tags must be unique"}
    return {"ok": True, "inbounds": len(config["inbounds"]), "outbounds": len(config["outbounds"])}


def apply_preview_only() -> dict[str, Any]:
    """Validate that a routing plan is representable without modifying live Xray.

    Live application is deliberately gated until the installation's actual PasarGuard
    core-config API is discovered. Directly editing generated configs would be overwritten
    by PasarGuard and could break node synchronization.
    """
    path = locate_config()
    if not path:
        return {"ok": False, "applied": False, "error": "Managed Xray config path was not detected"}
    result = validate_config(Path(path))
    audit("routing_preview", "success" if result["ok"] else "failed", result)
    return {**result, "applied": False, "reason": "safe API-managed application required"}
