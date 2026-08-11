from fastapi import APIRouter

from app.services.safety import recent_audit

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def audit_log() -> dict[str, object]:
    return {"events": recent_audit()}
