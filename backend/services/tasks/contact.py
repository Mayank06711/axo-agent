from backend.services.tasks.registry import TaskDefinition, TaskRegistry

contact_task = TaskDefinition(
    name="contact",
    display_name="Find Contact & Support Information",
    weight=0.20,
    success_indicators=[
        "contact", "support", "email", "phone",
        "chat", "help", "ticket", "sales",
        "address", "location", "office",
        "call", "reach", "connect",
    ],
    prompt=(
        "Find CONTACT and SUPPORT information for this website's product or service.\n\n"
        "Look for: email addresses, phone numbers, physical address, "
        "live chat or chatbot, support ticket system, contact form, "
        "sales contact, social media links, office locations.\n\n"
        "You are currently on the website's homepage."
    ),
)

TaskRegistry.register(contact_task)
