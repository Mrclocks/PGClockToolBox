from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.backup.scheduler import load, run_now, save
from app.services.telegram import config_from_env, send_backup


def tick() -> dict[str, object]:
    schedule = load()
    if not schedule.enabled:
        return {"status": "disabled"}
    now = datetime.now(timezone.utc)
    due_at = datetime.fromisoformat(schedule.last_run) + timedelta(hours=schedule.interval_hours) if schedule.last_run else now
    if now < due_at:
        return {"status": "waiting", "next": due_at.isoformat()}
    result = run_now()
    if result.get("status") == "success" and result.get("path"):
        token, chat_id, proxy = config_from_env()
        if token and chat_id:
            try:
                parts = send_backup(Path(str(result["path"])), token, chat_id, proxy, "PGClockToolBox scheduled backup")
                result["telegram_parts"] = parts
            except Exception as exc:
                schedule.last_status = "delivery_failed"
                schedule.last_error = str(exc)
                save(schedule)
                return {"status": "delivery_failed", "error": str(exc), "backup": result}
    return result


if __name__ == "__main__":
    print(tick())
