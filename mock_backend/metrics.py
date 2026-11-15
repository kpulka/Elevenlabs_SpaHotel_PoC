"""In-process metrics for ``GET /metrics`` (no dependencies, JSON output).

Per route: request count, transport errors split into 401 / 422 / 5xx, business rejections
(HTTP 200 with ``success: false``) and latency p50 / p95 over a bounded window of the most
recent samples. Counters live in process memory and reset on restart - enough to answer
"is the agent hitting errors, and which tool is slow?" during a pilot. A production deployment
would export the same numbers to Prometheus / OpenTelemetry.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

LATENCY_WINDOW = 500  # most recent samples kept per route


@dataclass
class RouteStats:
    requests: int = 0
    unauthorized_401: int = 0
    validation_422: int = 0
    server_5xx: int = 0
    business_rejections: int = 0
    latencies_ms: deque[float] = field(default_factory=lambda: deque(maxlen=LATENCY_WINDOW))

    def snapshot(self) -> dict[str, Any]:
        samples = sorted(self.latencies_ms)
        return {
            "requests": self.requests,
            "errors": {
                "unauthorized_401": self.unauthorized_401,
                "validation_422": self.validation_422,
                "server_5xx": self.server_5xx,
            },
            "business_rejections": self.business_rejections,
            "latency_ms": {
                "p50": percentile(samples, 50),
                "p95": percentile(samples, 95),
                "samples": len(samples),
            },
        }


def percentile(sorted_samples: list[float], percent: float) -> float | None:
    """Nearest-rank percentile of an already sorted list (``None`` when empty)."""
    if not sorted_samples:
        return None
    rank = max(1, -(-len(sorted_samples) * percent // 100))  # ceil without importing math
    return round(sorted_samples[int(rank) - 1], 3)


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._routes: dict[str, RouteStats] = {}
        self._counters: dict[str, int] = {}
        self._started = time.monotonic()

    def observe(self, route: str, status: int, duration_ms: float, rejected: bool = False) -> None:
        with self._lock:
            stats = self._routes.setdefault(route, RouteStats())
            stats.requests += 1
            stats.latencies_ms.append(duration_ms)
            if status == 401:
                stats.unauthorized_401 += 1
            elif status == 422:
                stats.validation_422 += 1
            elif status >= 500:
                stats.server_5xx += 1
            if rejected:
                stats.business_rejections += 1

    def increment(self, counter: str, amount: int = 1) -> None:
        """Named counter outside the per-route table (e.g. ``events.delivered``)."""
        with self._lock:
            self._counters[counter] = self._counters.get(counter, 0) + amount

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "uptime_seconds": round(time.monotonic() - self._started, 3),
                "latency_window": LATENCY_WINDOW,
                "routes": {route: stats.snapshot() for route, stats in sorted(self._routes.items())},
                "counters": dict(sorted(self._counters.items())),
            }

    def reset(self) -> None:
        with self._lock:
            self._routes.clear()
            self._counters.clear()
            self._started = time.monotonic()


METRICS = Metrics()
