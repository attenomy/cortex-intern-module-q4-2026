import time
from typing import Any

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

SERVICE_START_TIME = time.time()

REQUEST_COUNT = Counter(
    "cortex_requests_total",
    "Total HTTP requests received by Cortex",
    ["method", "route", "status"],
)

REQUEST_LATENCY = Histogram(
    "cortex_request_latency_seconds",
    "Observed HTTP request latency in seconds",
    buckets=[0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.0],
)

CACHE_HITS = Counter(
    "cortex_cache_hits_total",
    "Total semantic cache hits",
)

ACTIVE_WORKERS = Gauge(
    "cortex_active_workers",
    "Number of active semantic cache application lifespans",
)

UPTIME = Gauge(
    "cortex_uptime_seconds",
    "Total service uptime in seconds",
)


class TelemetryService:
    """Telemetry, Prometheus metrics and health monitoring service."""

    def get_health(self, is_model_ready: bool = True) -> dict[str, Any]:
        return {
            "status": "healthy",
            "service": "attenomy-cortex-engine",
            "version": "1.0.0",
            "model_loaded": is_model_ready,
            "uptime_seconds": round(time.time() - SERVICE_START_TIME, 2),
        }

    def get_metrics_prometheus(self) -> str:
        UPTIME.set(time.time() - SERVICE_START_TIME)
        return generate_latest().decode("utf-8")


def record_cache_hit() -> None:
    """Increment the semantic cache hit counter."""
    CACHE_HITS.inc()


def record_worker_started() -> None:
    """Record the start of a semantic cache application lifespan."""
    ACTIVE_WORKERS.inc()


def record_worker_stopped() -> None:
    """Record the end of a semantic cache application lifespan."""
    ACTIVE_WORKERS.dec()
