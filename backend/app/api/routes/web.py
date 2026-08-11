from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])
# web.py lives in backend/app/api/routes/; parents[2] is backend/app.
INDEX = Path(__file__).resolve().parents[2] / "web" / "index.html"


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    if not INDEX.is_file():
        raise HTTPException(status_code=500, detail=f"Dashboard missing at {INDEX}")
    return HTMLResponse(INDEX.read_text(encoding="utf-8"))
