from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from app.services.backup.engine import backup_result_dict, create_full_backup

router = APIRouter(prefix="/backup", tags=["backup"])

_last_result: dict[str, object] = {"status": "never_run"}


def _run_backup() -> None:
    global _last_result
    result = create_full_backup()
    _last_result = {"status": "success" if result.ok else "failed", **backup_result_dict(result)}


@router.get("/status")
async def backup_status() -> dict[str, object]:
    return _last_result


@router.post("/run")
async def run_backup(background_tasks: BackgroundTasks) -> dict[str, object]:
    if _last_result.get("status") == "running":
        return {"accepted": False, "status": "running"}
    _last_result.clear()
    _last_result.update({"status": "running"})
    background_tasks.add_task(_run_backup)
    return {"accepted": True, "status": "running"}
