from __future__ import annotations

import pytest

from app.services import dns


def test_dns_accepts_ipv4_and_ipv6():
    assert dns._valid_servers(["1.1.1.1", "2606:4700:4700::1111"]) == [
        "1.1.1.1",
        "2606:4700:4700::1111",
    ]


def test_dns_rejects_invalid_server():
    with pytest.raises(ValueError):
        dns._valid_servers(["not-an-ip"])


def test_dns_rejects_empty_and_too_many():
    with pytest.raises(ValueError):
        dns._valid_servers([])
    with pytest.raises(ValueError):
        dns._valid_servers(["1.1.1.1"] * 5)


def test_dns_reads_nameservers(tmp_path, monkeypatch):
    path = tmp_path / "resolv.conf"
    path.write_text("nameserver 1.1.1.1\nnameserver 1.1.1.1\nnameserver 8.8.8.8\n")
    monkeypatch.setattr(dns, "RESOLV_CONF", path)
    assert dns._resolv_conf_servers() == ["1.1.1.1", "8.8.8.8"]
