from fastapi import APIRouter, HTTPException

from .schemas import CacheLookupRequest, CacheLookupResponse, CacheStatsResponse
from .service import SemanticCacheService

router = APIRouter(prefix="/cache", tags=["Semantic Caching"])
service = SemanticCacheService()

@router.post("/lookup", response_model=CacheLookupResponse)
def lookup_cache_endpoint(req: CacheLookupRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return service.lookup(req.query, req.threshold)

@router.get("/stats", response_model=CacheStatsResponse)
def get_cache_stats_endpoint():
    return service.get_stats()

