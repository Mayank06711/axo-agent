from collections import defaultdict
from typing import Callable

from backend.schemas.simulation import AgentEvent


class EventBus:
    """In-process pub/sub. Agents emit events, listeners react."""

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable):
        """Register a listener. Use '*' to listen to all events."""
        self._listeners[event_type].append(callback)

    async def emit(self, event: AgentEvent):
        """Dispatch event to matching listeners + wildcard listeners."""
        for cb in self._listeners.get(event.event_type.value, []):
            await cb(event)
        for cb in self._listeners.get("*", []):
            await cb(event)
