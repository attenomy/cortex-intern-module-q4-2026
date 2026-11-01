from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

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

class DocumentExtractionRequest(BaseModel):
    document_id: str
    document_type: str = Field(..., description="Document type, e.g. invoice, receipt, contract")
    raw_content: str

class ExtractionResponse(BaseModel):
    document_id: str
    extracted_fields: Dict[str, Any]
    schema_valid: bool
    latency_ms: float

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_loaded: bool
    uptime_seconds: float
