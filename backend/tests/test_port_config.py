from pathlib import Path


def test_web_port_is_7100_everywhere():
    root = Path(__file__).resolve().parents[1].parent
    service = (root / "systemd" / "pgclocktoolbox.service").read_text(encoding="utf-8")
    installer = (root / "install.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "--port 7100" in service
    assert 'PORT="${PGCLOCK_PORT:-7100}"' in installer
    assert ":7100/" in readme or ":7100" in readme
    assert ":6000/" not in readme


def test_installer_supports_uninstall_and_restart():
    installer = (Path(__file__).resolve().parents[1].parent / "install.sh").read_text(encoding="utf-8")
    assert "cmd_uninstall" in installer
    assert "uninstall" in installer
    assert "systemctl restart" in installer
    assert "verify_panel" in installer
    assert "--purge" in installer
