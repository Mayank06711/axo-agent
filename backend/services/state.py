import time
from abc import ABC, abstractmethod

import redis.asyncio as aioredis

from backend.schemas.simulation import AgentEvent, SimulationReport, TaskResult

CACHE_TTL = 1800  # 30 minutes


class SimulationStore(ABC):
    """Storage interface — swap Redis for Postgres without changing callers."""

    @abstractmethod
    async def save(self, sim_id: str, report: SimulationReport) -> None: ...

    @abstractmethod
    async def get(self, sim_id: str) -> SimulationReport | None: ...

    @abstractmethod
    async def update_status(self, sim_id: str, status: str) -> None: ...

    @abstractmethod
    async def append_task_result(self, sim_id: str, result: TaskResult) -> None: ...

    @abstractmethod
    async def list_recent(self, limit: int = 20) -> list[SimulationReport]: ...

    @abstractmethod
    async def append_event(self, sim_id: str, event: AgentEvent) -> None: ...

    @abstractmethod
    async def get_events(self, sim_id: str) -> list[dict]: ...


class RedisSimulationStore(SimulationStore):
    """Redis implementation — fast, ephemeral, 30-min TTL."""

    TTL = CACHE_TTL

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def save(self, sim_id: str, report: SimulationReport) -> None:
        await self.redis.set(
            f"simulation:{sim_id}", report.model_dump_json(), ex=self.TTL
        )
        await self.redis.zadd("simulations:recent", {sim_id: time.time()})

    async def get(self, sim_id: str) -> SimulationReport | None:
        data = await self.redis.get(f"simulation:{sim_id}")
        if not data:
            return None
        return SimulationReport.model_validate_json(data)

    async def update_status(self, sim_id: str, status: str) -> None:
        report = await self.get(sim_id)
        if report:
            report.status = status
            await self.save(sim_id, report)

    async def append_task_result(self, sim_id: str, result: TaskResult) -> None:
        report = await self.get(sim_id)
        if report:
            report.task_results.append(result)
            await self.save(sim_id, report)

    async def list_recent(self, limit: int = 20) -> list[SimulationReport]:
        sim_ids = await self.redis.zrevrange("simulations:recent", 0, limit - 1)
        reports = []
        for sim_id in sim_ids:
            report = await self.get(sim_id)
            if report:
                reports.append(report)
        return reports

    async def append_event(self, sim_id: str, event: AgentEvent) -> None:
        key = f"simulation:{sim_id}:log"
        await self.redis.rpush(key, event.model_dump_json())
        await self.redis.expire(key, self.TTL)

    async def get_events(self, sim_id: str) -> list[dict]:
        import json

        key = f"simulation:{sim_id}:log"
        raw_events = await self.redis.lrange(key, 0, -1)
        return [json.loads(e) for e in raw_events]
