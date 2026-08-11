from app.services.backup.scheduler import BackupSchedule, configure


def test_schedule_validation(monkeypatch, tmp_path):
    import app.services.backup.scheduler as scheduler
    monkeypatch.setattr(scheduler, "CONFIG", tmp_path / "schedule.json")
    value = configure(True, 24, 7)
    assert value.enabled is True
    assert value.interval_hours == 24
    try:
        configure(True, 5, 7)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported interval must fail")
