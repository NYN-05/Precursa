import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
            try:
                await agent_task
            except asyncio.CancelledError:
                pass
        await redis_client.close()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, lifespan=lifespan)

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router)

    # UI Configuration
    frontend_dist = "frontend/dist"
    static_dir = "static"

    # Serve static assets from frontend/dist if it exists
    if os.path.exists(frontend_dist):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="frontend-assets")

    @app.get("/{rest_of_path:path}", include_in_schema=False)
    async def ui_fallback(rest_of_path: str):
        # 1. Try to find the file in frontend/dist
        if os.path.exists(frontend_dist):
            file_path = os.path.join(frontend_dist, rest_of_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
        
        # 2. Try to find the file in static folder
        file_path = os.path.join(static_dir, rest_of_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # 3. Fallback to index.html (SPA routing)
        # Only if it doesn't look like an API call
        if not rest_of_path.startswith(settings.api_v1_prefix.lstrip("/")):
            frontend_index = os.path.join(frontend_dist, "index.html")
            if os.path.exists(frontend_index):
                return FileResponse(frontend_index)
            
            static_index = os.path.join(static_dir, "index.html")
            if os.path.exists(static_index):
                return FileResponse(static_index)

        # 4. Final 404
        raise HTTPException(status_code=404)

    return app


app = create_app()
