from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl

T = TypeVar("T")


# ── Standard API response wrapper ───────────────────────────


class ResponseMetadata(BaseModel):
    request_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class APIResponse(BaseModel, Generic[T]):
    status_code: int = 200
    message: str = "success"
    data: T | None = None
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class EventType(str, Enum):
    SIMULATION_START = "SIMULATION_START"
    SIMULATION_COMPLETE = "SIMULATION_COMPLETE"
    SIMULATION_ERROR = "SIMULATION_ERROR"
    TASK_START = "TASK_START"
    TASK_COMPLETE = "TASK_COMPLETE"
    TASK_ERROR = "TASK_ERROR"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    LLM_THINKING = "LLM_THINKING"
    STANDARDS_CHECK_START = "STANDARDS_CHECK_START"
    STANDARDS_CHECK_RESULT = "STANDARDS_CHECK_RESULT"
    STANDARDS_CHECK_DONE = "STANDARDS_CHECK_DONE"


# ── Request / Response ──────────────────────────────────────


class SimulationRequest(BaseModel):
    url: HttpUrl
    tasks: list[str] = ["pricing", "features", "documentation", "contact"]
    llm_provider: str | None = None  # optional — resolved from config if not provided
    llm_model: str | None = None  # optional — resolved from config if not provided


class SimulationStartResponse(BaseModel):
    simulation_id: str
    status: str = "pending"
    stream_url: str


# ── Events (SSE payload) ────────────────────────────────────


class AgentEvent(BaseModel):
    simulation_id: str
    timestamp: datetime
    event_type: EventType
    task_name: str | None = None
    agent_name: str | None = None
    data: dict[str, Any] = {}


# ── Agent structured output (returned by LLM via response_format) ──


class AgentFinding(BaseModel):
    """A single piece of information the agent found on a page."""

    content: str = Field(description="The factual data found, verbatim from the page")
    source_url: str = Field(description="The URL where this was found")


class TaskAgentOutput(BaseModel):
    """Structured output every worker agent must produce via response_format."""

    found: bool = Field(description="Was the requested information found on the site?")
    confidence: str = Field(
        description="How confident: 'high' (clearly found), 'medium' (partially found), 'low' (uncertain), 'none' (not found)"
    )
    findings: list[AgentFinding] = Field(
        default_factory=list,
        description="List of factual data points found. Empty if nothing found.",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Problems encountered: login walls, CAPTCHAs, 404s, blocked pages, missing pages",
    )
    summary: str = Field(
        description="Brief factual summary of what was found or why it was not found"
    )


# ── LLM task score evaluation (used by hybrid scorer) ───────


class TaskScoreEvaluation(BaseModel):
    """LLM evaluates the quality of an agent's task result. Used by Scorer."""

    found_score: int = Field(
        description="0-40. Did the agent find the requested information? 0=not found, 40=clearly found"
    )
    confidence_score: int = Field(
        description="0-25. How reliable is the data? 0=unreliable/vague, 25=specific and verifiable"
    )
    accessibility_score: int = Field(
        description="0-20. How easy was it to find? 20=immediately visible, 0=required many steps or failed"
    )
    data_quality_score: int = Field(
        description="0-15. How complete and useful is the extracted data? 0=empty/useless, 15=comprehensive and actionable"
    )
    reasoning: str = Field(
        description="Brief explanation of why you assigned these scores"
    )


# ── Task result ─────────────────────────────────────────────


class TaskResult(BaseModel):
    task_name: str
    found: bool
    confidence: float = 0
    accessibility: float = 0
    data_quality: float = 0
    score: float = 0
    findings: list[str] = []
    issues: list[str] = []
    steps_taken: int = 0
    raw_data: dict[str, Any] = {}


# ── Standards check result ──────────────────────────────────


class StandardsCheckResult(BaseModel):
    check_name: str
    score: float = 0
    details: dict[str, Any] = {}
    issues: list[str] = []


# ── Full report ─────────────────────────────────────────────


class SimulationReport(BaseModel):
    simulation_id: str
    url: str
    status: str = "pending"
    overall_score: float = 0
    grade: str = "F"
    task_results: list[TaskResult] = []
    standards_results: list[StandardsCheckResult] = []
    issues: list[str] = []
    recommendations: list[str] = []
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    llm_provider: str = ""
    llm_model: str = ""
