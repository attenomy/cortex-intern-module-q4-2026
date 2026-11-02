from typing import Any

from pydantic import BaseModel, Field


class CacheLookupRequest(BaseModel):
    query: str = Field(..., description="Query to search in semantic cache")
    threshold: float = Field(default=0.95, ge=0.5, le=1.0)

class CacheLookupResponse(BaseModel):
    hit: bool
    matched_query: str | None = None
    similarity_score: float | None = None
    cached_payload: dict[str, Any] | None = None
    latency_ms: float

class CacheStatsResponse(BaseModel):
    total_entries: int
    hit_rate: float
    redis_connected: bool

