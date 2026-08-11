from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])
# index.html lives in backend/app/web/; parents[1] resolves to backend/app.
INDEX = Path(__file__).resolve().parents[1] / "web" / "index.html"


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> str:
    return INDEX.read_text(encoding="utf-8")
