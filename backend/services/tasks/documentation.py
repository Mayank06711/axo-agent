from backend.services.tasks.registry import TaskDefinition, TaskRegistry

documentation_task = TaskDefinition(
    name="documentation",
    display_name="Find Documentation & Help Resources",
    weight=0.25,
    success_indicators=[
        "doc", "documentation", "guide", "tutorial",
        "api reference", "getting started", "quickstart",
        "help", "faq", "knowledge base", "developer",
        "sdk", "library", "changelog", "reference",
    ],
    prompt=(
        "Find DOCUMENTATION, HELP, and DEVELOPER RESOURCES for this website's product or service.\n\n"
        "Look for: API documentation, developer guides, getting-started tutorials, "
        "SDK/library references, FAQ or help center, knowledge base, "
        "changelogs, status pages.\n\n"
        "You are currently on the website's homepage."
    ),
)

TaskRegistry.register(documentation_task)
