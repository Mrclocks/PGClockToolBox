from fastapi import FastAPI

from app.api.routes.discovery import router as discovery_router
from app.api.routes.health import router as health_router
from app.api.routes.system import router as system_router
from app.api.routes.web import router as web_router

app = FastAPI(title="PGClockToolBox", version="0.1.0", docs_url="/api/docs", redoc_url="/api/redoc")
app.include_router(health_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(discovery_router, prefix="/api")
app.include_router(web_router)


@app.get("/api")
async def api_root() -> dict[str, str]:
    return {"name": "PGClockToolBox", "version": app.version}
