from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app.services.auth import ensure_token, valid

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    token: str


@router.get("/setup")
async def setup_status() -> dict[str, bool]:
    # Never return the token. The installer creates it once and the operator can
    # read it locally with root privileges.
    return {"configured": bool(ensure_token())}


@router.post("/login")
async def login(payload: LoginRequest, response: Response) -> dict[str, bool]:
    if not valid(payload.token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    response.set_cookie("pgclock_session", payload.token, httponly=True, secure=False, samesite="strict", max_age=86400)
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie("pgclock_session")
    return {"ok": True}
