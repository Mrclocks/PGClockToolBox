from pathlib import Path

from app.services.backup import detector


def test_detect_sqlite_from_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    data = tmp_path / "data"
    data.mkdir()
    (data / "db.sqlite3").write_bytes(b"SQLite format 3\x00")
    monkeypatch.setattr(detector, "PASARGUARD_ENV", env)
    monkeypatch.setattr(detector, "PASARGUARD_DATA", data)
    assert detector.detect_database()["engine"] == "sqlite"


def test_detect_postgresql_without_leaking_url(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('SQLALCHEMY_DATABASE_URL="postgresql+asyncpg://user:secret@db/pasarguard"\n', encoding="utf-8")
    monkeypatch.setattr(detector, "PASARGUARD_ENV", env)
    monkeypatch.setattr(detector, "PASARGUARD_DATA", tmp_path / "data")
    result = detector.detect_database()
    assert result == {"engine": "postgresql", "source": "env"}
    assert "secret" not in str(result)
