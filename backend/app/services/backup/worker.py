from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.backup.scheduler import load, run_now, save
from app.services.telegram import config_from_env, send_document


def tick() -> dict[str, object]:
    schedule = load()
    if not schedule.enabled:
        return {"status": "disabled"}
    now = datetime.now(timezone.utc)
    due = not schedule.last_run or now >= datetime.fromisoformat(schedule.last_run) + timedelta(hours=schedule.interval_hours)
    if not due:
        return {"status": "waiting", "next": (datetime.fromisoformat(schedule.last_run) + timedelta(hours=schedule.interval_hours)).isoformat()}
    result = run_now()
    if result.get("status") == "success" and result.get("path"):
        token, chat_id, proxy = config_from_env()
        if token and chat_id:
            try:
                send_document(__import__("pathlib").Path(str(result["path"])), token, chat_id, proxy, "PGClockToolBox scheduled backup")
            except Exception as exc:
                schedule.last_status = "delivery_failed"
                schedule.last_error = str(exc)
                save(schedule)
                return {"status": "delivery_failed", "error": str(exc)}
    return result

if __name__ == "__main__":
    print(tick())
