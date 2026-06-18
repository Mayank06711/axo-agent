# Import all task modules to trigger TaskRegistry.register() at import time
from backend.services.tasks import contact, documentation, features, pricing  # noqa: F401
