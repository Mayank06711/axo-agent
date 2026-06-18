import logging
from datetime import datetime, timezone

from langgraph.prebuilt import create_react_agent

from backend.config import settings
from backend.events.bus import EventBus
from backend.schemas.simulation import AgentEvent, EventType, TaskAgentOutput
from backend.services.fetcher.playwright_fetcher import PlaywrightFetcher
from backend.services.llm.factory import get_llm
from backend.services.tasks.registry import TaskDefinition
from backend.services.tools.browser_tools import create_browser_tools
from backend.services.worker_prompt import WORKER_SYSTEM_PROMPT

logger = logging.getLogger("axo_agent.worker")


async def run_worker_agent(
    task: TaskDefinition,
    target_url: str,
    simulation_id: str,
    event_bus: EventBus,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
) -> dict:
    """
    Run a single worker agent for one task.
    Each worker gets its own browser instance for isolation.
    Streams all events (tool calls, LLM thinking) via EventBus.
    Captures structured response from the same stream — single invocation.
    """
    fetcher = PlaywrightFetcher()
    await fetcher.launch()

    try:
        await fetcher.goto(target_url)

        tools = create_browser_tools(fetcher)
        llm = get_llm(llm_provider, llm_model)

        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=WORKER_SYSTEM_PROMPT,
            response_format=TaskAgentOutput,
        )

        await event_bus.emit(
            AgentEvent(
                simulation_id=simulation_id,
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.TASK_START,
                task_name=task.name,
                agent_name=f"worker_{task.name}",
                data={
                    "url": target_url,
                    "task_display_name": task.display_name,
                },
            )
        )

        tool_call_count = 0
        thinking_buffer = ""
        structured_response = None
        user_message = f"Target website: {target_url}\n\n{task.prompt}"

        async for event in agent.astream_events(
            {"messages": [("user", user_message)]},
            version="v2",
        ):
            kind = event["event"]

            # ── Tool call start ──
            if kind == "on_tool_start":
                # Flush any accumulated thinking before the tool call
                if thinking_buffer.strip():
                    await event_bus.emit(
                        AgentEvent(
                            simulation_id=simulation_id,
                            timestamp=datetime.now(timezone.utc),
                            event_type=EventType.LLM_THINKING,
                            task_name=task.name,
                            agent_name=f"worker_{task.name}",
                            data={"text": thinking_buffer.strip()},
                        )
                    )
                    thinking_buffer = ""

                tool_call_count += 1
                await event_bus.emit(
                    AgentEvent(
                        simulation_id=simulation_id,
                        timestamp=datetime.now(timezone.utc),
                        event_type=EventType.TOOL_CALL,
                        task_name=task.name,
                        agent_name=f"worker_{task.name}",
                        data={
                            "tool": event.get("name", "unknown"),
                            "input": str(
                                event.get("data", {}).get("input", "")
                            )[:200],
                            "call_number": tool_call_count,
                        },
                    )
                )

            # ── Tool call end ──
            elif kind == "on_tool_end":
                output_str = str(event.get("data", {}).get("output", ""))
                await event_bus.emit(
                    AgentEvent(
                        simulation_id=simulation_id,
                        timestamp=datetime.now(timezone.utc),
                        event_type=EventType.TOOL_RESULT,
                        task_name=task.name,
                        agent_name=f"worker_{task.name}",
                        data={
                            "tool": event.get("name", "unknown"),
                            "output": output_str[:300],
                        },
                    )
                )

            # ── LLM streaming tokens (thinking / reasoning) ──
            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk", None)
                if chunk:
                    content = getattr(chunk, "content", "") or ""
                    tool_calls = getattr(chunk, "tool_calls", []) or []

                    # Only buffer text content (not tool call decisions)
                    # Also skip if content looks like JSON (structured output step)
                    if content and not tool_calls and not content.startswith("{"):
                        thinking_buffer += content

            # ── Capture structured response from chain end ──
            elif kind == "on_chain_end":
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict) and "structured_response" in output:
                    structured_response = output["structured_response"]

            # Enforce max tool calls
            if tool_call_count >= settings.max_tool_calls_per_task:
                break

        # Flush remaining thinking buffer
        if thinking_buffer.strip():
            await event_bus.emit(
                AgentEvent(
                    simulation_id=simulation_id,
                    timestamp=datetime.now(timezone.utc),
                    event_type=EventType.LLM_THINKING,
                    task_name=task.name,
                    agent_name=f"worker_{task.name}",
                    data={"text": thinking_buffer.strip()},
                )
            )

        # Build output from structured response
        if structured_response and hasattr(structured_response, "model_dump"):
            output_data = structured_response.model_dump()
        elif structured_response and isinstance(structured_response, dict):
            output_data = structured_response
        else:
            output_data = {
                "found": False,
                "confidence": "low",
                "findings": [],
                "issues": ["Agent did not produce structured output"],
                "summary": thinking_buffer[:500] if thinking_buffer else "No output",
            }

        await event_bus.emit(
            AgentEvent(
                simulation_id=simulation_id,
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.TASK_COMPLETE,
                task_name=task.name,
                agent_name=f"worker_{task.name}",
                data={
                    "found": output_data.get("found", False),
                    "confidence": output_data.get("confidence", "none"),
                    "summary": output_data.get("summary", ""),
                    "tool_calls_used": tool_call_count,
                },
            )
        )

        return {
            "task_name": task.name,
            "output": output_data,
            "tool_call_count": tool_call_count,
            "success": True,
        }

    except Exception as e:
        logger.exception(f"Worker error for task '{task.name}': {e}")

        await event_bus.emit(
            AgentEvent(
                simulation_id=simulation_id,
                timestamp=datetime.now(timezone.utc),
                event_type=EventType.TASK_ERROR,
                task_name=task.name,
                agent_name=f"worker_{task.name}",
                data={"error": str(e)},
            )
        )

        return {
            "task_name": task.name,
            "output": {
                "found": False,
                "confidence": "none",
                "findings": [],
                "issues": [f"Agent error: {str(e)}"],
                "summary": f"Agent failed: {str(e)}",
            },
            "tool_call_count": 0,
            "success": False,
        }

    finally:
        await fetcher.close()
