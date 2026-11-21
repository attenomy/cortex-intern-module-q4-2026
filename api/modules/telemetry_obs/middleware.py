
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .service import REQUEST_COUNT, REQUEST_LATENCY


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Collect HTTP request counts and latency."""

    async def dispatch(self, request: Request, call_next):
        # Avoid counting Prometheus scrape requests.
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start_time

            route = request.scope.get("route")
            route_path = getattr(route, "path", "unmatched")

            REQUEST_COUNT.labels(
                method=request.method,
                route=route_path,
                status=str(status_code),
            ).inc()

            REQUEST_LATENCY.observe(duration)
