from fastapi import APIRouter

from app.services.installation import discover_installation

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("")
async def installation_discovery() -> dict[str, object]:
    return discover_installation()
