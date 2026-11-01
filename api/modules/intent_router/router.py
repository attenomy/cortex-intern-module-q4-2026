from fastapi import APIRouter, HTTPException
from .schemas import QueryRoutingRequest, RoutingDecision
from .service import SemanticRouter

router = APIRouter(prefix="/router", tags=["Intent Routing"])
service = SemanticRouter()

@router.post("", response_model=RoutingDecision)
def route_query_endpoint(req: QueryRoutingRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    return service.route_query(req.query, req.client_tier)
