from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class CacheLookupRequest(BaseModel):
    query: str = Field(..., description="Query to search in semantic cache")
    threshold: float = Field(default=0.95, ge=0.5, le=1.0)

class CacheLookupResponse(BaseModel):
    hit: bool
    matched_query: Optional[str] = None
    similarity_score: Optional[float] = None
    cached_payload: Optional[Dict[str, Any]] = None
    latency_ms: float

class CacheStatsResponse(BaseModel):
    total_entries: int
    hit_rate: float
    redis_connected: bool
