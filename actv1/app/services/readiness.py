from starlette.concurrency import run_in_threadpool

from app.db.session import check_db_connection
from app.services.redis_client import redis_client


async def check_readiness() -> dict[str, str]:
    db_ok = await run_in_threadpool(check_db_connection)
    redis_ok = await redis_client.ping()

    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "database": "ok" if db_ok else "down",
        "redis": "ok" if redis_ok else "down",
    }
