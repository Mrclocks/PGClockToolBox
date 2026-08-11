from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.backup import router as backup_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.dns import router as dns_router
from app.api.routes.health import router as health_router
from app.api.routes.nodes import router as nodes_router
from app.api.routes.optimizer import router as optimizer_router
from app.api.routes.recovery import router as recovery_router
from app.api.routes.routing import router as routing_router
from app.api.routes.system import router as system_router
from app.api.routes.warp import router as warp_router
from app.api.routes.web import router as web_router
from app.services.auth import valid

app = FastAPI(title="PGClockToolBox", version="0.9.0", docs_url="/api/docs", redoc_url="/api/redoc")
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(discovery_router, prefix="/api")
app.include_router(backup_router, prefix="/api")
app.include_router(dns_router, prefix="/api")
app.include_router(optimizer_router, prefix="/api")
app.include_router(warp_router, prefix="/api")
app.include_router(nodes_router, prefix="/api")
app.include_router(routing_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(recovery_router, prefix="/api")
app.include_router(web_router)


@app.middleware("http")
async def require_admin(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        public = {"/api/health", "/api/auth/setup", "/api/auth/login", "/api/auth/logout"}
        if request.url.path not in public:
            token = request.headers.get("X-Admin-Token") or request.cookies.get("pgclock_session")
            if not valid(token):
                return JSONResponse({"detail": "Authentication required"}, status_code=401)
    return await call_next(request)


@app.get("/api")
async def api_root() -> dict[str, str]:
    return {"name": "PGClockToolBox", "version": app.version}
