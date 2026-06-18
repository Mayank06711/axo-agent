from uuid import uuid4

import redis.asyncio as aioredis

from backend.config import settings


async def get_redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def generate_simulation_id() -> str:
    return f"sim_{uuid4().hex[:12]}"
