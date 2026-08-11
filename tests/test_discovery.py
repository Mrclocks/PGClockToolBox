from app.services.discovery import discover


def test_discovery_returns_expected_shape() -> None:
    result = discover().as_dict()
    expected = {
        "os_name",
        "os_version",
        "architecture",
        "kernel",
        "pasarguard_installed",
        "pasarguard_root",
        "pasarguard_data",
        "xray_installed",
        "wireguard_installed",
        "docker_installed",
        "docker_compose_installed",
        "database_hint",
    }
    assert set(result) == expected
