from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.routing.engine import Rule, add, defaults, load, remove, save

router = APIRouter(prefix="/routing", tags=["routing"])

class RuleInput(BaseModel):
    kind: str
    value: str
    action: str
    ports: list[int] | None = None
    protocol: str = Field(default="tcp,udp")

@router.get("/rules")
async def rules() -> dict[str, object]:
    return {"rules": [r.__dict__ if hasattr(r, "__dict__") else {"kind": r.kind, "value": r.value, "action": r.action, "ports": r.ports, "protocol": r.protocol} for r in load()]}

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
    return {"rules": [{"kind": r.kind, "value": r.value, "action": r.action, "ports": r.ports, "protocol": r.protocol} for r in result]}

@router.delete("/rules/{index}")
async def delete_rule(index: int) -> dict[str, object]:
    try:
        result = remove(index)
    except IndexError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"rules": [{"kind": r.kind, "value": r.value, "action": r.action, "ports": r.ports, "protocol": r.protocol} for r in result]}
