import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.init_data import seed_default_roles_and_admin
from app.db.session import SessionLocal
from app.services.agent_service import agent_tick_loop
from app.services.redis_client import redis_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    agent_task: asyncio.Task | None = None
    if settings.seed_on_startup:
        with SessionLocal() as db:
            try:
                seed_default_roles_and_admin(db)
                logger.info("Startup seed completed")
            except Exception as exc:  # pragma: no cover
                logger.warning("Startup seed skipped: %s", exc)
    if settings.agent_autostart:
        agent_task = asyncio.create_task(agent_tick_loop())
    try:
        yield
    finally:
        if agent_task is not None:
            agent_task.cancel()
        await redis_client.close()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, lifespan=lifespan)
    app.include_router(api_router)
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

    return app


app = create_app()
