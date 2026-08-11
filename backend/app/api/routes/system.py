from fastapi import APIRouter

from app.services.discovery import discover

router = APIRouter(tags=["system"])


@router.get("/system/discovery")
async def system_discovery() -> dict[str, object]:
    return discover().as_dict()
