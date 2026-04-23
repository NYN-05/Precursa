from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from hashlib import sha256
import random
import time
from typing import Any


@dataclass
class SlidingWindowRateLimiter:
    max_per_second: int
    max_per_hour: int
    max_per_day: int
    min_interval_seconds: float = field(init=False)
    _timestamps: deque[float] = field(default_factory=deque, init=False)
    _last_request_at: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.min_interval_seconds = 1.0 / max(1, self.max_per_second)

    def allow(self) -> bool:
        now = time.time()

        if now - self._last_request_at < self.min_interval_seconds:
            return False

        one_hour_ago = now - 3600
        one_day_ago = now - 86400

        while self._timestamps and self._timestamps[0] < one_day_ago:
            self._timestamps.popleft()

        hourly_count = sum(1 for timestamp in self._timestamps if timestamp >= one_hour_ago)
        if hourly_count >= self.max_per_hour or len(self._timestamps) >= self.max_per_day:
            return False

        self._last_request_at = now
        self._timestamps.append(now)
        return True


@dataclass
class TimedCache:
    ttl_seconds: int
    _values: dict[str, tuple[Any, float]] = field(default_factory=dict, init=False)

    def get(self, key: str) -> Any | None:
        entry = self._values.get(key)
        if not entry:
            return None

        value, timestamp = entry
        if time.time() - timestamp > self.ttl_seconds:
            self._values.pop(key, None)
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        self._values[key] = (value, time.time())


def stable_seed(*parts: Any) -> int:
    digest = sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def seeded_choice(items: list[Any], *seed_parts: Any) -> Any:
    if not items:
        raise ValueError("items must not be empty")

    rng = random.Random(stable_seed(*seed_parts))
    return items[rng.randrange(len(items))]


def seeded_sample(items: list[Any], sample_size: int, *seed_parts: Any) -> list[Any]:
    if not items:
        return []

    size = min(len(items), max(1, sample_size))
    rng = random.Random(stable_seed(*seed_parts))
    indices = list(range(len(items)))
    rng.shuffle(indices)
    return [items[index] for index in indices[:size]]
