import json

from app.services.routing.engine import Rule, validate_rule
from app.services.routing.xray import _rule_to_xray, validate_config


def test_domain_rule_compiles_to_xray_domain():
    item = _rule_to_xray(Rule("domain", "google.com", "warp"))
    assert item["type"] == "field"
    assert item["outboundTag"] == "pgclock-warp"
    assert item["domain"] == ["google.com"]


def test_invalid_domain_is_rejected():
    try:
        validate_rule(Rule("domain", "not a domain", "warp"))
    except ValueError:
        return
    raise AssertionError("invalid domain was accepted")


def test_xray_config_validation(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"inbounds": [{"tag": "in"}], "outbounds": [{"tag": "direct"}]}))
    result = validate_config(path)
    assert result["ok"] is True
