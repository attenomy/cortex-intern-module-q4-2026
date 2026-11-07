
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CacheLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., description="Query to search")
    threshold: float = Field(default=0.95, ge=0.5, le=1.0)


class CacheStoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(...)
    payload: dict[str, Any]
    ttl_seconds: int | None = Field(default=None, gt=0)

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("Payload cannot be empty")
        return value


class CacheLookupResponse(BaseModel):
    hit: bool
    matched_query: str | None = None
    similarity_score: float
    cached_payload: dict[str, Any] | None = None
    latency_ms: float
    embedding_latency_ms: float = 0.0
    redis_latency_ms: float = 0.0
    timings: dict[str, float] | None = None


class CacheStoreResponse(BaseModel):
    stored: bool
    message: str


class CacheStatsResponse(BaseModel):
    total_entries: int
    hit_rate: float
    redis_connected: bool
