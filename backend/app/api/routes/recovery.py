from fastapi import APIRouter

from app.services.health.healer import heal

router = APIRouter(prefix="/recovery", tags=["recovery"])


@router.post("/heal")
async def auto_heal() -> dict[str, object]:
    return heal()
