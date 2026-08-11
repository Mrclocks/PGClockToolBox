from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.routing.engine import Rule, add, defaults, load, remove, save
from app.services.routing.xray import apply_preview_only, preview

router = APIRouter(prefix="/routing", tags=["routing"])


class RuleInput(BaseModel):
    kind: str
    value: str
    action: str
    ports: list[int] | None = None
    protocol: str = Field(default="tcp,udp")


def _dict(rule: Rule) -> dict[str, object]:
    return {"kind": rule.kind, "value": rule.value, "action": rule.action, "ports": rule.ports, "protocol": rule.protocol}


@router.get("/rules")
async def rules() -> dict[str, object]:
    return {"rules": [_dict(r) for r in load()]}


@router.post("/defaults")
async def install_defaults() -> dict[str, object]:
    save(defaults())
    return await rules()


@router.post("/rules")
async def create_rule(data: RuleInput) -> dict[str, object]:
    try:
        result = add(Rule(**data.model_dump()))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"rules": [_dict(r) for r in result]}


@router.delete("/rules/{index}")
async def delete_rule(index: int) -> dict[str, object]:
    try:
        result = remove(index)
    except IndexError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"rules": [_dict(r) for r in result]}


@router.get("/xray/preview")
async def xray_preview() -> dict[str, object]:
    return preview()


@router.post("/xray/validate")
async def xray_validate() -> dict[str, object]:
    return apply_preview_only()
