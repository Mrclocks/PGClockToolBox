from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import warp

router = APIRouter(prefix="/warp", tags=["warp"])


class HostRule(BaseModel):
    host: str


class IpRule(BaseModel):
    cidr: str


@router.get("/status")
async def warp_status() -> dict[str, object]:
    return asdict(warp.status())


@router.post("/install")
async def warp_install() -> dict[str, object]:
    try:
        warp.install()
        return {"ok": True, "status": asdict(warp.status())}
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/register")
async def warp_register() -> dict[str, object]:
    try:
        warp.register()
        return {"ok": True, "status": asdict(warp.status())}
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/connect")
async def warp_connect() -> dict[str, object]:
    try:
        warp.connect()
        return {"ok": True, "status": asdict(warp.status())}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/disconnect")
async def warp_disconnect() -> dict[str, object]:
    try:
        warp.disconnect()
        return {"ok": True}
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/host")
async def warp_host(rule: HostRule) -> dict[str, object]:
    try:
        warp.add_host(rule.host)
        return {"ok": True, "host": rule.host}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/host")
async def warp_host_remove(rule: HostRule) -> dict[str, object]:
    try:
        warp.remove_host(rule.host)
        return {"ok": True, "host": rule.host}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ip")
async def warp_ip(rule: IpRule) -> dict[str, object]:
    try:
        warp.add_ip(rule.cidr)
        return {"ok": True, "cidr": rule.cidr}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/ip")
async def warp_ip_remove(rule: IpRule) -> dict[str, object]:
    try:
        warp.remove_ip(rule.cidr)
        return {"ok": True, "cidr": rule.cidr}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
