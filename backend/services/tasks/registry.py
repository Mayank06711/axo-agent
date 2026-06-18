from dataclasses import dataclass, field


@dataclass
class TaskDefinition:
    name: str
    display_name: str
    prompt: str
    weight: float
    success_indicators: list[str] = field(default_factory=list)


class TaskRegistry:
    """Registry pattern — add new agent tasks without changing orchestrator."""

    _tasks: dict[str, TaskDefinition] = {}

    @classmethod
    def register(cls, task: TaskDefinition):
        cls._tasks[task.name] = task

    @classmethod
    def get(cls, name: str) -> TaskDefinition:
        if name not in cls._tasks:
            raise KeyError(
                f"Task '{name}' not registered. Available: {list(cls._tasks.keys())}"
            )
        return cls._tasks[name]

    @classmethod
    def get_all(cls) -> list[TaskDefinition]:
        return list(cls._tasks.values())

    @classmethod
    def get_names(cls) -> list[str]:
        return list(cls._tasks.keys())
