import asyncio
import json
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from backend.schemas.simulation import (
    APIResponse,
    EventType,
    SimulationReport,
    SimulationRequest,
    SimulationStartResponse,
)
from backend.services.llm.factory import resolve_provider_and_model
from backend.services.state import RedisSimulationStore
from backend.utils.helpers import generate_simulation_id

logger = logging.getLogger("axo_agent.routes")

router = APIRouter(tags=["simulation"])


@router.post("/simulate")
async def start_simulation(
    body: SimulationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    sim_id = generate_simulation_id()

    # Resolve provider/model early — validates credentials are configured
    llm_provider, llm_model = resolve_provider_and_model(
        body.llm_provider, body.llm_model
    )
    logger.info("sim=%s | POST /simulate | url=%s provider=%s model=%s",
                sim_id, body.url, llm_provider, llm_model)

    store = RedisSimulationStore(request.app.state.redis)

    report = SimulationReport(
        simulation_id=sim_id,
        url=str(body.url),
        status="pending",
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    await store.save(sim_id, report)

    from backend.services.orchestrator import run_simulation

    background_tasks.add_task(run_simulation, sim_id, body, request.app.state.redis)

    return APIResponse(
        status_code=201,
        message="Simulation started",
        data=SimulationStartResponse(
            simulation_id=sim_id,
            status="pending",
            stream_url=f"/api/simulate/{sim_id}/stream",
        ),
    )


@router.get("/simulate/{simulation_id}")
async def get_simulation(simulation_id: str, request: Request):
    store = RedisSimulationStore(request.app.state.redis)
    report = await store.get(simulation_id)
    if not report:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return APIResponse(
        status_code=200,
        message="success",
        data=report,
    )


@router.get("/simulate/{simulation_id}/events")
async def get_simulation_events(simulation_id: str, request: Request):
    """Fetch stored event log for a past simulation (available for 30 min)."""
    store = RedisSimulationStore(request.app.state.redis)
    events = await store.get_events(simulation_id)
    if not events:
        raise HTTPException(status_code=404, detail="No events found for this simulation")

    return APIResponse(
        status_code=200,
        message="success",
        data=events,
    )


@router.get("/simulate/{simulation_id}/stream")
async def stream_simulation(simulation_id: str, request: Request):
    logger.info("sim=%s | SSE stream connected", simulation_id)
    redis = request.app.state.redis

    async def event_generator():
        pubsub = redis.pubsub()
        channel = f"simulation:{simulation_id}:events"
        await pubsub.subscribe(channel)
        logger.info("sim=%s | subscribed to channel %s", simulation_id, channel)

        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    data = message["data"]
                    event = json.loads(data)
                    event_type = event.get("event_type", "message")
                    logger.debug("sim=%s | SSE event: %s", simulation_id, event_type)

                    yield {"data": data}

                    if event_type in (
                        EventType.SIMULATION_COMPLETE.value,
                        EventType.SIMULATION_ERROR.value,
                    ):
                        logger.info("sim=%s | SSE stream closing on %s", simulation_id, event_type)
                        break
                else:
                    yield {"comment": "heartbeat"}

                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            logger.info("sim=%s | SSE stream disconnected", simulation_id)

    return EventSourceResponse(event_generator())
