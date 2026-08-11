from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import dns

router = APIRouter(prefix="/dns", tags=["dns"])


class DnsRequest(BaseModel):
    servers: list[str] = Field(min_length=1, max_length=4)


@router.get("/status")
async def dns_status() -> dict[str, object]:
    return dns.status_dict()


@router.post("/apply")
async def dns_apply(payload: DnsRequest) -> dict[str, object]:
    try:
        return {"ok": True, "status": dns.status_dict(dns.apply(payload.servers))}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/restore")
async def dns_restore() -> dict[str, object]:
    try:
        return {"ok": True, "status": dns.status_dict(dns.restore())}
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
