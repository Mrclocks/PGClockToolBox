from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.backup.engine import backup_result_dict, create_full_backup
from app.services.backup.scheduler import configure, load, run_now
from app.services.telegram import send_document

router = APIRouter(prefix="/backup", tags=["backup"])
_last_result: dict[str, object] = {"status": "never_run"}

class ScheduleRequest(BaseModel):
    enabled: bool
    interval_hours: int
    retention: int = 7

class TelegramRequest(BaseModel):
    token: str
    chat_id: str
    proxy: str | None = None


def _run_backup() -> None:
    global _last_result
    result = create_full_backup()
    _last_result = {"status": "success" if result.ok else "failed", **backup_result_dict(result)}

@router.get("/status")
async def backup_status() -> dict[str, object]:
    return {"last": _last_result, "schedule": load().__dict__ if hasattr(load(), "__dict__") else {"enabled": load().enabled, "interval_hours": load().interval_hours, "retention": load().retention, "last_run": load().last_run, "last_status": load().last_status, "last_error": load().last_error}}

@router.post("/run")
async def run_backup(background_tasks: BackgroundTasks) -> dict[str, object]:
    if _last_result.get("status") == "running":
        return {"accepted": False, "status": "running"}
    _last_result.clear(); _last_result.update({"status": "running"})
    background_tasks.add_task(_run_backup)
    return {"accepted": True, "status": "running"}

@router.post("/schedule")
async def schedule_backup(payload: ScheduleRequest) -> dict[str, object]:
    try:
        value = configure(payload.enabled, payload.interval_hours, payload.retention)
        return {"ok": True, "enabled": value.enabled, "interval_hours": value.interval_hours, "retention": value.retention}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/telegram")
async def configure_telegram(payload: TelegramRequest) -> dict[str, object]:
    if len(payload.token) < 20 or len(payload.chat_id) > 256:
        raise HTTPException(status_code=400, detail="Invalid Telegram configuration")
    import os
    from app.core.paths import TOOLBOX_DATA
    path = TOOLBOX_DATA / "telegram.env"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"PGCLOCK_TELEGRAM_BOT_TOKEN={payload.token}\nPGCLOCK_TELEGRAM_CHAT_ID={payload.chat_id}\nPGCLOCK_TELEGRAM_PROXY={payload.proxy or ''}\n", encoding="utf-8")
    path.chmod(0o600)
    return {"ok": True}

@router.post("/telegram/test")
async def telegram_test() -> dict[str, object]:
    from app.core.paths import TOOLBOX_BACKUPS, TOOLBOX_DATA
    from app.services.telegram import config_from_env
    token, chat_id, proxy = config_from_env()
    env_file = TOOLBOX_DATA / "telegram.env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                if k == "PGCLOCK_TELEGRAM_BOT_TOKEN": token = v
                elif k == "PGCLOCK_TELEGRAM_CHAT_ID": chat_id = v
                elif k == "PGCLOCK_TELEGRAM_PROXY": proxy = v
    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="Telegram is not configured")
    candidates = sorted(TOOLBOX_BACKUPS.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise HTTPException(status_code=404, detail="Create a backup first")
    try:
        send_document(candidates[0], token, chat_id, proxy, "PGClockToolBox backup test")
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
