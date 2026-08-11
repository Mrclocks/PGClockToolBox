from fastapi import APIRouter

from app.services.health.monitor import snapshot

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    return snapshot()
