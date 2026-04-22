import json
from typing import Any

import redis

from app.core.config import settings


class LiveStateCache:
    def __init__(self, redis_url: str, key_prefix: str, ttl_seconds: int) -> None:
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds
        self._client: redis.Redis | None = None
        self._fallback_store: dict[str, str] = {}

    def _cache_key(self, shipment_key: str) -> str:
        return f"{self._key_prefix}:{shipment_key}"

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    def set_state(self, shipment_key: str, payload: dict[str, Any]) -> None:
        key = self._cache_key(shipment_key)
        serialized = json.dumps(payload, default=str, separators=(",", ":"), sort_keys=True)

        # Keep a process-local fallback so tests and degraded environments can still read state.
        self._fallback_store[key] = serialized

        try:
            self.client.setex(key, self._ttl_seconds, serialized)
        except Exception:
            return

    def get_state(self, shipment_key: str) -> dict[str, Any] | None:
        key = self._cache_key(shipment_key)

        serialized: str | None = None
        try:
            serialized = self.client.get(key)
        except Exception:
            serialized = None

        if serialized is None:
            serialized = self._fallback_store.get(key)

        if serialized is None:
            return None

        try:
            return json.loads(serialized)
        except json.JSONDecodeError:
            return None


live_state_cache = LiveStateCache(
    redis_url=settings.redis_url,
    key_prefix=settings.state_cache_key_prefix,
    ttl_seconds=settings.state_cache_ttl_seconds,
)
