
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST

from .schemas import HealthResponse
from .service import TelemetryService

router = APIRouter(tags=["Telemetry & Observability"])
service = TelemetryService()


@router.get("/health", response_model=HealthResponse)
def health_check_endpoint():
    return service.get_health()


@router.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics_endpoint():
    return PlainTextResponse(
        content=service.get_metrics_prometheus(),
        media_type=CONTENT_TYPE_LATEST,
    )

