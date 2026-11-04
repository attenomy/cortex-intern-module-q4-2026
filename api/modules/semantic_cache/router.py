from fastapi import APIRouter, HTTPException

from .schemas import (
    CacheLookupRequest,
    CacheLookupResponse,
    CacheStoreRequest,
    CacheStoreResponse,
    CacheStatsResponse,
)
from .service import SemanticCacheService


router = APIRouter(
    prefix="/cache",
    tags=["Semantic Caching"]
)

service = SemanticCacheService()


@router.post("/lookup", response_model=CacheLookupResponse)
def lookup_cache_endpoint(req: CacheLookupRequest):
    if not req.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    return service.lookup(
        req.query,
        req.threshold
    )


@router.post("/store", response_model=CacheStoreResponse)
def store_cache_endpoint(req: CacheStoreRequest):
    if not req.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    try:
        service.store(
            query=req.query,
            payload=req.payload,
            ttl_seconds=req.ttl_seconds
        )

        return {
            "stored": True,
            "message": "Query successfully stored in semantic cache"
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to store data in Redis semantic cache"
        )


@router.get("/stats", response_model=CacheStatsResponse)
def get_cache_stats_endpoint():
    return service.get_stats()