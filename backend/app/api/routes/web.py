from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])
# web.py lives in backend/app/api/routes/; parents[2] is backend/app.
INDEX = Path(__file__).resolve().parents[2] / "web" / "index.html"


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> str:
    return INDEX.read_text(encoding="utf-8")
