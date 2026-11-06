
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure API directory is accessible in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.doc_extractor.router import router as doc_extractor_router
from modules.doc_ingestion.router import router as doc_ingestion_router
from modules.intent_router.router import router as intent_router
from modules.semantic_cache.router import (
    router as semantic_cache_router,
)
from modules.semantic_cache.router import (
    service as semantic_cache_service,
)
from modules.telemetry_obs.router import router as telemetry_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    logger.info("Starting Attenomy Cortex API")

    try:
        await asyncio.to_thread(
            semantic_cache_service.warm_up
        )
        logger.info("Semantic cache model warmed up successfully")

    except Exception:
        logger.exception(
            "Semantic cache warm-up failed. "
            "Model loading can retry on demand."
        )

    yield

    try:
        await asyncio.to_thread(
            semantic_cache_service.redis_client.close
        )
        logger.info("Semantic cache Redis connection closed")

    except Exception:
        logger.exception("Redis shutdown cleanup failed")


app = FastAPI(
    title="Attenomy Cortex Engine API",
    description="Enterprise Autonomous Multi-Agent Orchestration & Cognitive Knowledge Retrieval Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Modular Routers
app.include_router(intent_router, prefix="/api/v1")
app.include_router(doc_extractor_router, prefix="/api/v1")
app.include_router(semantic_cache_router, prefix="/api/v1")
app.include_router(doc_ingestion_router, prefix="/api/v1")
app.include_router(telemetry_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
