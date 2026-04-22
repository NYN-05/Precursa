from __future__ import annotations

from collections import Counter
from time import perf_counter
from typing import Any


class ObservabilityRegistry:
    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()
        self._latencies: dict[str, list[float]] = {}

    def increment(self, name: str, amount: float = 1.0) -> None:
        self._counters[name] += amount

    def observe_latency(self, name: str, seconds: float) -> None:
        self._latencies.setdefault(name, []).append(seconds)

    def snapshot(self) -> dict[str, Any]:
        latency_summary: dict[str, dict[str, float]] = {}
        for name, values in self._latencies.items():
            if not values:
                continue
            ordered = sorted(values)
            p95_index = min(len(ordered) - 1, int(len(ordered) * 0.95))
            latency_summary[name] = {
                "count": float(len(ordered)),
                "avg": round(sum(ordered) / len(ordered), 6),
                "p95": round(ordered[p95_index], 6),
                "max": round(max(ordered), 6),
            }

        return {
            "counters": dict(self._counters),
            "latencies": latency_summary,
        }

    def prometheus_text(self) -> str:
        lines: list[str] = []
        for name, value in sorted(self._counters.items()):
            lines.append(f"precursa_{name} {float(value)}")
        for name, values in sorted(self._latencies.items()):
            if values:
                lines.append(f"precursa_{name}_seconds_count {float(len(values))}")
                lines.append(f"precursa_{name}_seconds_avg {sum(values) / len(values):.6f}")
        return "\n".join(lines) + "\n"


class latency_timer:
    def __init__(self, name: str) -> None:
        self._name = name
        self._started = 0.0

    def __enter__(self) -> None:
        self._started = perf_counter()

    def __exit__(self, *_: object) -> None:
        metrics.observe_latency(self._name, perf_counter() - self._started)


metrics = ObservabilityRegistry()
