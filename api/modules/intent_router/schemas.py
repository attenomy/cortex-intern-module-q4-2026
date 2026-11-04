from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

FALLBACK_THRESHOLD = 0.60


class IntentCategory(str, Enum):
    FINANCE = "finance"
    SUPPORT = "support"
    SEARCH = "search"
    ORCHESTRATION = "orchestration"


class TopKCandidate(BaseModel):
    intent_category: IntentCategory
    confidence: float = Field(ge=0.0, le=1.0)


class IntentRoutingRequest(BaseModel):
    # extra="forbid": unknown fields are rejected (422) instead of silently ignored.
    model_config = ConfigDict(extra="forbid")

    # No min_length on purpose: empty / whitespace-only queries are rejected by the
    # router with HTTP 400 (existing behaviour and existing tests).
    query: str = Field(
        ...,
        max_length=10_000,
        strict=True,
        description="User search query or agent input prompt",
    )
    client_tier: str = Field(default="Enterprise", description="Client tier (Starter, Pro, Enterprise, VIP)")
    max_routing_candidates: int = Field(default=3, ge=1, le=10)


# Backward-compatible alias: router.py and any other callers keep working.
QueryRoutingRequest = IntentRoutingRequest


class RoutingDecision(BaseModel):
    intent_category: IntentCategory
    confidence: float = Field(ge=0.0, le=1.0)  # top-1 softmax probability
    fallback_triggered: bool = False
    target_pipeline: str
    top_k: list[TopKCandidate] = Field(default_factory=list)
    latency_ms: float = Field(ge=0.0)
    cached: bool = False

    @model_validator(mode="after")
    def check_invariants(self) -> "RoutingDecision":
        if self.fallback_triggered and (
            self.intent_category != IntentCategory.SEARCH or self.confidence >= FALLBACK_THRESHOLD
        ):
            raise ValueError("fallback requires intent 'search' and confidence < 0.60")
        probs = [c.confidence for c in self.top_k]
        if probs != sorted(probs, reverse=True):
            raise ValueError("top_k must be sorted by confidence, descending")
        return self
