from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.admin import router as admin_router
from app.api.auth import client_router
from app.api.auth import router as auth_router
from app.api.billing import router as billing_router
from app.api.cases import router as cases_router
from app.api.clients import router as clients_router
from app.api.dashboard import router as dashboard_router
from app.api.documents import router as documents_router
from app.core.config import get_settings
from app.db import check_database
from app.seed import seed_demo_data

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env in {"development", "demo"}:
        await seed_demo_data()
    yield


app = FastAPI(
    title="LawFirm ERP API",
    version="0.1.0",
    description="Backoffice ERP API for law firms.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(client_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(clients_router, prefix="/api/v1")


@app.get("/health", tags=["system"], summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["system"], summary="Readiness probe")
async def ready() -> JSONResponse:
    try:
        await check_database()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": {"database": "failed"}},
        )
    return JSONResponse(content={"status": "ready", "checks": {"database": "ok"}})
