import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException

from .schemas import QueryRoutingRequest, RoutingDecision
from .service import ModelNotReady, SemanticRouter

logger = logging.getLogger(__name__)
service = SemanticRouter()


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
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    service.ensure_loaded()   # no-op once the lifespan has loaded the model
    try:
        return service.route_query(req.query, req.client_tier, req.max_routing_candidates)
    except ModelNotReady:
        raise HTTPException(status_code=503, detail="Intent router model is not ready")
    except Exception:
        logger.exception("intent routing failed")
        raise HTTPException(status_code=500, detail="Internal routing error")
