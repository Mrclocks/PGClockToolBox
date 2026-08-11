from __future__ import annotations

import ipaddress
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.paths import TOOLBOX_DATA

STATE = TOOLBOX_DATA / "routing.json"
DOMAIN_RE = re.compile(r"^(?:\*\.)?[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")

@dataclass(slots=True)
class Rule:
    kind: str
    value: str
    action: str
    ports: list[int] | None = None
    protocol: str = "tcp,udp"


def _valid_domain(value: str) -> bool:
    return bool(DOMAIN_RE.fullmatch(value.lower().rstrip(".")))


def validate_rule(rule: Rule) -> None:
    if rule.kind not in {"domain", "ip", "cidr", "geoip", "geosite", "port"}:
        raise ValueError("unsupported rule type")
    if rule.action not in {"direct", "warp", "proxy"}:
        raise ValueError("unsupported routing action")
    if rule.kind == "domain" and not _valid_domain(rule.value):
        raise ValueError("invalid domain")
    if rule.kind in {"ip", "cidr"}:
        ipaddress.ip_network(rule.value, strict=False)
    if rule.kind == "port":
        port = int(rule.value)
        if not 1 <= port <= 65535:
            raise ValueError("invalid port")
    if rule.ports and any(not 1 <= p <= 65535 for p in rule.ports):
        raise ValueError("invalid destination port")
    if rule.protocol not in {"tcp", "udp", "tcp,udp"}:
        raise ValueError("invalid protocol")


def load() -> list[Rule]:
    try:
        raw = json.loads(STATE.read_text(encoding="utf-8"))
        return [Rule(**item) for item in raw.get("rules", [])]
    except (OSError, ValueError, TypeError):
        return []


def save(rules: list[Rule]) -> None:
    for rule in rules:
        validate_rule(rule)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"rules": [asdict(r) for r in rules]}, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE)


def add(rule: Rule) -> list[Rule]:
    rules = load()
    validate_rule(rule)
    if not any(asdict(r) == asdict(rule) for r in rules):
        rules.append(rule)
    save(rules)
    return rules


def remove(index: int) -> list[Rule]:
    rules = load()
    if index < 0 or index >= len(rules):
        raise IndexError("routing rule not found")
    rules.pop(index)
    save(rules)
    return rules


def defaults() -> list[Rule]:
    return [
        Rule("domain", "google.com", "warp"),
        Rule("domain", "youtube.com", "warp"),
        Rule("domain", "gemini.google.com", "warp"),
        Rule("domain", "spotify.com", "warp"),
        Rule("domain", "openai.com", "warp"),
        Rule("domain", "chatgpt.com", "warp"),
    ]
