import redis.asyncio as aioredis

from backend.events.bus import EventBus
from backend.schemas.simulation import AgentEvent
from backend.services.state import CACHE_TTL


class RedisEventPublisher:
    """Observer that forwards all EventBus events to Redis Pub/Sub + persists to log."""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def publish(self, event: AgentEvent):
        event_json = event.model_dump_json()
        channel = f"simulation:{event.simulation_id}:events"
        log_key = f"simulation:{event.simulation_id}:log"

        # Pub/Sub for live SSE streaming
        await self.redis.publish(channel, event_json)

        # Persist to list for later retrieval
        await self.redis.rpush(log_key, event_json)
        await self.redis.expire(log_key, CACHE_TTL)

    def setup(self, event_bus: EventBus):
        """Subscribe to all events on the bus."""
        event_bus.subscribe("*", self.publish)
