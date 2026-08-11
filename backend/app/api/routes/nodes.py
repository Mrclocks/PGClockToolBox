from __future__ import annotations

from fastapi import APIRouter

from app.services.nodes import discover_local_nodes

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("")
async def nodes() -> dict[str, object]:
    return {"nodes": discover_local_nodes()}
