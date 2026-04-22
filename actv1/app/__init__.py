import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from db.init_data import seed_default_roles_and_admin
from app.db.session import SessionLocal
from app.services.redis_client import redis_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.seed_on_startup:
        with SessionLocal() as db:
            try:
                seed_default_roles_and_admin(db)
                logger.info("Startup seed completed")
            except Exception as exc:  # pragma: no cover
                logger.warning("Startup seed skipped: %s", exc)
    yield
    await redis_client.close()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, lifespan=lifespan)
    app.include_router(api_router)

    return app


app = create_app()
