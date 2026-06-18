import asyncio
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from backend.events.bus import EventBus
from backend.events.redis_publisher import RedisEventPublisher
from backend.schemas.simulation import (
    AgentEvent,
    EventType,
    SimulationReport,
    SimulationRequest,
)
from backend.services.checks.agents_json import check_agents_json
from backend.services.checks.llms_txt import check_llms_txt
from backend.services.checks.meta_tags import check_meta_tags
from backend.services.checks.robots_txt import check_robots_txt
from backend.services.checks.schema_org import check_schema_org
from backend.services.checks.security import check_security
from backend.services.llm.factory import get_llm, resolve_provider_and_model
from backend.services.scorer import Scorer
from backend.services.state import RedisSimulationStore
from backend.services.tasks import *  # noqa: F401,F403 — triggers task registration
from backend.services.tasks.registry import TaskRegistry
from backend.services.worker import run_worker_agent

logger = logging.getLogger("axo_agent.orchestrator")


async def run_simulation(
    simulation_id: str,
    request: SimulationRequest,
    redis_client: aioredis.Redis,
):
    """Main orchestration — runs agent tasks + standards checks, scores, reports."""
    event_bus = EventBus()
    publisher = RedisEventPublisher(redis_client)
    publisher.setup(event_bus)

    store = RedisSimulationStore(redis_client)
    target_url = str(request.url)
    started_at = datetime.now(timezone.utc)

    # Resolve provider/model once — validates credentials are configured
    llm_provider, llm_model = resolve_provider_and_model(
        request.llm_provider, request.llm_model
    )

    logger.info("sim=%s | starting | url=%s provider=%s model=%s tasks=%s",
                simulation_id, target_url, llm_provider, llm_model, request.tasks)

    # Allow SSE client time to subscribe before emitting events.
    # Redis Pub/Sub does not buffer — events sent before subscriber connects are lost.
    await asyncio.sleep(1)

    await store.update_status(simulation_id, "running")

    await event_bus.emit(
        AgentEvent(
            simulation_id=simulation_id,
            timestamp=started_at,
            event_type=EventType.SIMULATION_START,
            data={"url": target_url, "tasks": request.tasks},
        )
    )

    try:
        # ── 1. Run agent tasks sequentially (each gets own browser) ──
        task_worker_results = []

        for task_name in request.tasks:
            try:
                task_def = TaskRegistry.get(task_name)
            except KeyError:
                logger.warning(f"Unknown task '{task_name}', skipping")
                continue

            logger.info("sim=%s | task=%s | starting worker", simulation_id, task_name)
            worker_result = await run_worker_agent(
                task=task_def,
                target_url=target_url,
                simulation_id=simulation_id,
                event_bus=event_bus,
                llm_provider=llm_provider,
                llm_model=llm_model,
            )
            logger.info("sim=%s | task=%s | worker done | found=%s calls=%d",
                        simulation_id, task_name,
                        worker_result.get("output", {}).get("found"),
                        worker_result.get("tool_call_count", 0))
            task_worker_results.append((task_def, worker_result))

        logger.info("sim=%s | all tasks done | running standards checks", simulation_id)
        # ── 2. Run standards checks in parallel (httpx, no browser) ──
        await event_bus.emit(
            AgentEvent(
                simulation_id=simulation_id,
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.STANDARDS_CHECK_START,
                data={
                    "checks": [
                        "robots_txt", "llms_txt", "schema_org",
                        "meta_tags", "agents_json", "security",
                    ]
                },
            )
        )

        standards_results = await asyncio.gather(
            check_robots_txt(target_url),
            check_llms_txt(target_url),
            check_schema_org(target_url),
            check_meta_tags(target_url),
            check_agents_json(target_url),
            check_security(target_url),
        )

        for sc in standards_results:
            await event_bus.emit(
                AgentEvent(
                    simulation_id=simulation_id,
                    timestamp=datetime.now(timezone.utc),
                    event_type=EventType.STANDARDS_CHECK_RESULT,
                    data={
                        "check_name": sc.check_name,
                        "score": sc.score,
                        "issues": sc.issues,
                    },
                )
            )

        await event_bus.emit(
            AgentEvent(
                simulation_id=simulation_id,
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.STANDARDS_CHECK_DONE,
                data={},
            )
        )

        # ── 3. Score everything (hybrid: LLM for tasks, deterministic for standards) ──
        llm = get_llm(llm_provider, llm_model)
        scorer = Scorer(llm)

        task_results = []
        for task_def, worker_result in task_worker_results:
            scored = await scorer.score_task(task_def, worker_result, target_url)
            task_results.append(scored)

        all_task_defs = [td for td, _ in task_worker_results]
        overall_score, grade = scorer.calculate_overall(
            task_results, list(standards_results), all_task_defs
        )

        recommendations = scorer.generate_recommendations(
            task_results, list(standards_results)
        )

        all_issues = []
        for tr in task_results:
            all_issues.extend(tr.issues)
        for sc in standards_results:
            all_issues.extend(sc.issues)

        # ── 4. Build final report ──
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()

        report = SimulationReport(
            simulation_id=simulation_id,
            url=target_url,
            status="completed",
            overall_score=overall_score,
            grade=grade,
            task_results=task_results,
            standards_results=list(standards_results),
            issues=all_issues,
            recommendations=recommendations,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=round(duration, 1),
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

        await store.save(simulation_id, report)

        logger.info("sim=%s | completed | score=%.1f grade=%s duration=%.1fs",
                    simulation_id, overall_score, grade, duration)

        await event_bus.emit(
            AgentEvent(
                simulation_id=simulation_id,
                timestamp=completed_at,
                event_type=EventType.SIMULATION_COMPLETE,
                data={
                    "overall_score": overall_score,
                    "grade": grade,
                    "duration_seconds": round(duration, 1),
                },
            )
        )

    except Exception as e:
        logger.exception(f"Simulation {simulation_id} failed: {e}")

        await store.update_status(simulation_id, "failed")

        await event_bus.emit(
            AgentEvent(
                simulation_id=simulation_id,
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.SIMULATION_ERROR,
                data={"error": str(e)},
            )
        )
