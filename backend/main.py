import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.exception_handlers import register_exception_handlers
from backend.api.routes.simulation import router as simulation_router
from backend.config import settings
from backend.schemas.simulation import APIResponse
from backend.utils.helpers import get_redis_client

# ── Logging setup ────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-25s | %(message)s"
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
for noisy in ("httpx", "httpcore", "openai", "playwright", "urllib3", "langsmith"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger("axo_agent.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await get_redis_client()
    await app.state.redis.ping()
    logger.info("startup complete | redis=%s", settings.redis_url)
    yield
    await app.state.redis.aclose()
    logger.info("shutdown complete")


app = FastAPI(
    title="AXO Agent",
    description="Synthetic Agent Simulation - AI Agent Readiness Testing",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(simulation_router, prefix="/api")


@app.get("/health")
async def health():
    redis_status = "disconnected"
    try:
        await app.state.redis.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "error"

    return APIResponse(
        status_code=200,
        message="healthy",
        data={"redis": redis_status},
    )
