from backend.services.tasks.registry import TaskDefinition, TaskRegistry

pricing_task = TaskDefinition(
    name="pricing",
    display_name="Find Pricing Information",
    weight=0.30,
    success_indicators=[
        "price", "pricing", "cost", "plan", "tier",
        "free", "premium", "enterprise", "pro",
        "$", "per month", "annually", "subscription",
        "starter", "basic", "billing",
    ],
    prompt=(
        "Find PRICING information for this website's product or service.\n\n"
        "Look for: plan/tier names, prices, billing periods (monthly/annual), "
        "free trial or free tier availability, feature differences between tiers, "
        "enterprise or custom pricing options.\n\n"
        "You are currently on the website's homepage."
    ),
)

TaskRegistry.register(pricing_task)
