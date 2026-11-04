
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class CacheLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., description="Query to search")
    threshold: float = Field(default=0.95, ge=0.5, le=1.0)


class CacheStoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(...)
    payload: Dict[str, Any]
    ttl_seconds: Optional[int] = Field(default=None, gt=0)

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value:
            raise ValueError("Payload cannot be empty")
        return value


class CacheLookupResponse(BaseModel):
    hit: bool
    matched_query: Optional[str] = None
    similarity_score: float
    cached_payload: Optional[Dict[str, Any]] = None
    latency_ms: float
    embedding_latency_ms: float = 0.0
    redis_latency_ms: float = 0.0
    timings: Optional[Dict[str, float]] = None


class CacheStoreResponse(BaseModel):
    stored: bool
    message: str


class CacheStatsResponse(BaseModel):
    total_entries: int
    hit_rate: float
    redis_connected: bool
