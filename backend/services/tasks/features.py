from backend.services.tasks.registry import TaskDefinition, TaskRegistry

features_task = TaskDefinition(
    name="features",
    display_name="Find Product Features",
    weight=0.25,
    success_indicators=[
        "feature", "capability", "integration", "benefit",
        "solution", "platform", "tool", "automat",
        "dashboard", "analytics", "api", "workflow",
        "security", "compliance", "support",
    ],
    prompt=(
        "Find PRODUCT FEATURES and CAPABILITIES of this website's product or service.\n\n"
        "Look for: core features, key capabilities, integrations with other tools, "
        "technical specifications, use cases, product differentiators, "
        "platform components.\n\n"
        "You are currently on the website's homepage."
    ),
)

TaskRegistry.register(features_task)
