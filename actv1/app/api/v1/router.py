from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.protected import router as protected_router
from app.api.v1.risk import router as risk_router
from app.api.v1.state import router as state_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix=settings.api_v1_prefix)
api_router.include_router(ingestion_router, prefix=settings.api_v1_prefix)
api_router.include_router(protected_router, prefix=settings.api_v1_prefix)
api_router.include_router(state_router, prefix=settings.api_v1_prefix)
api_router.include_router(risk_router, prefix=settings.api_v1_prefix)
