from pathlib import Path


def test_dashboard_entrypoint_exists():
    index = Path(__file__).resolve().parents[1] / "app" / "web" / "index.html"
    assert index.is_file()
    assert "PGClockToolBox" in index.read_text(encoding="utf-8")


def test_web_route_resolves_entrypoint():
    route_file = Path(__file__).resolve().parents[1] / "app" / "api" / "routes" / "web.py"
    source = route_file.read_text(encoding="utf-8")
    assert 'parents[2] / "web" / "index.html"' in source
    assert "HTMLResponse" in source

    from app.api.routes.web import INDEX

    expected = Path(__file__).resolve().parents[1] / "app" / "web" / "index.html"
    assert INDEX.resolve() == expected.resolve()
    assert INDEX.is_file()
