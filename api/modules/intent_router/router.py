import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from .metrics import RouterMetrics
from .schemas import QueryRoutingRequest, RoutingDecision
from .service import ModelNotReady, SemanticRouter

logger = logging.getLogger(__name__)
service = SemanticRouter()
metrics = RouterMetrics()


@asynccontextmanager
async def lifespan(_app):
    """Load + warm up the model at startup. Never crash the shared API if it fails:
    the endpoint answers 503 until the model is available."""
    try:
        service.load()
    except Exception:
        logger.exception("intent router failed to load; /router will answer 503")
    yield


router = APIRouter(prefix="/router", tags=["Intent Routing"], lifespan=lifespan)


@router.post("", response_model=RoutingDecision)
def route_query_endpoint(req: QueryRoutingRequest):
    if not req.query.strip():
        metrics.record("bad_request")
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    service.ensure_loaded()   # no-op once the lifespan has loaded the model
    try:
        result = service.route_query(req.query, req.client_tier, req.max_routing_candidates)
    except ModelNotReady:
        metrics.record("not_ready")
        raise HTTPException(status_code=503, detail="Intent router model is not ready")
    except Exception:
        metrics.record("error")
        logger.exception("intent routing failed")
        raise HTTPException(status_code=500, detail="Internal routing error")
    metrics.record("fallback" if result["fallback_triggered"] else "routed",
                   result["intent_category"], result["latency_ms"])
    return result


@router.get("/metrics", response_class=PlainTextResponse)
def router_metrics_endpoint():
    return metrics.render(service.is_ready)
