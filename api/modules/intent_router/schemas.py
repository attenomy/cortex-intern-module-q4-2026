from pydantic import BaseModel, Field


class QueryRoutingRequest(BaseModel):
    query: str = Field(..., description="User search query or agent input prompt")
    client_tier: str = Field(default="Enterprise", description="Client tier (Starter, Pro, Enterprise, VIP)")
    max_routing_candidates: int = Field(default=3, ge=1, le=10)

class RoutingDecision(BaseModel):
    intent_category: str
    confidence: float
    target_pipeline: str
    latency_ms: float
    cached: bool = False

