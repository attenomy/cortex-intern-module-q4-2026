import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException

from .schemas import (
    CacheLookupRequest,
    CacheLookupResponse,
    CacheStatsResponse,
    CacheStoreRequest,
    CacheStoreResponse,
)
from .service import SemanticCacheService

logger = logging.getLogger(__name__)

service = SemanticCacheService()


@asynccontextmanager
async def semantic_cache_lifespan(app):
    """
    Preload the embedding model at startup and close Redis
    connections during application shutdown.
    """
    try:
        await asyncio.to_thread(service.warm_up)
        logger.info(
            "Semantic cache embedding model warmed up successfully."
        )
    except Exception:
        logger.exception(
            "Semantic cache warm-up failed. Lazy loading remains available."
        )

    try:
        yield
    finally:
        try:
            await asyncio.to_thread(service.redis_client.close)
            logger.info("Semantic cache Redis client closed.")
        except Exception:
            logger.exception(
                "Failed to close semantic cache Redis client."
            )


router = APIRouter(
    prefix="/cache",
    tags=["Semantic Caching"],
    lifespan=semantic_cache_lifespan,
)


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
        logger.exception("Semantic cache store operation failed.")
        raise HTTPException(
            status_code=503,
            detail="Unable to store data in Redis semantic cache"
        )


@router.get("/stats", response_model=CacheStatsResponse)
def get_cache_stats_endpoint():
    return service.get_stats()
