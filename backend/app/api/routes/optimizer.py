from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.services import optimizer

router = APIRouter(prefix="/optimizer", tags=["optimizer"])


@router.get("/status")
async def optimizer_status() -> dict[str, object]:
    return asdict(optimizer.status())


@router.post("/apply")
async def optimizer_apply() -> dict[str, object]:
    try:
        return {"ok": True, "status": asdict(optimizer.apply())}
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
