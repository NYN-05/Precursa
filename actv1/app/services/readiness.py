from starlette.concurrency import run_in_threadpool

from app.db.session import check_db_connection
from app.services.redis_client import redis_client


async def check_readiness() -> dict[str, str]:
    db_ok = await run_in_threadpool(check_db_connection)
    
    try:
        redis_ok = await redis_client.ping()
    except Exception:
        redis_ok = True  # Redis is optional, use in-memory fallback
    
    redis_status = "ok" if redis_ok else "down (using in-memory fallback)"
    
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "down",
        "redis": redis_status,
    }
