from pathlib import Path


def test_web_port_is_7100_everywhere():
    root = Path(__file__).resolve().parents[1]
    service = (root / "systemd" / "pgclocktoolbox.service").read_text(encoding="utf-8")
    installer = (root / "install.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "--port 7100" in service
    assert 'PORT="7100"' in installer
    assert ":7100/" in readme
    assert ":6000/" not in readme
