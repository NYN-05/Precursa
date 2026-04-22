import redis.asyncio as redis

from app.core.config import settings


class RedisClient:
    def __init__(self, url: str):
        self._url = url
        self._client: redis.Redis | None = None
        self._enabled = bool(url and url.strip())

    @property
    def client(self) -> redis.Redis:
        if self._client is None and self._enabled:
            try:
                self._client = redis.from_url(
                    self._url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except Exception:
                self._enabled = False
        return self._client

    async def ping(self) -> bool:
        if not self._enabled:
            return True  # Redis is optional
        try:
            if self._client is None:
                return False
            return bool(await self._client.ping())
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


redis_client = RedisClient(settings.redis_url)
