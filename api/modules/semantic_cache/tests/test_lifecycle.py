import asyncio
from importlib import import_module
from unittest.mock import patch

from modules.telemetry_obs.service import ACTIVE_WORKERS

cache_router = import_module("modules.semantic_cache.router")


def test_semantic_cache_lifecycle_tracks_worker():
    initial_value = ACTIVE_WORKERS._value.get()

    with (
        patch.object(cache_router.service, "warm_up"),
        patch.object(cache_router.service.redis_client, "close"),
    ):

        async def run_lifespan():
            async with cache_router.semantic_cache_lifespan(None):
                assert ACTIVE_WORKERS._value.get() == initial_value + 1

        asyncio.run(run_lifespan())

    assert ACTIVE_WORKERS._value.get() == initial_value
