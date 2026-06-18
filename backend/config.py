from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve .env relative to this file's directory (backend/)
_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6380/0"

    # LLM providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_version: str = "2025-01-01-preview"
    azure_openai_deployment: str = "gpt-4.1-nano"

    # LLM defaults
    default_llm_provider: str = "azure"
    default_llm_model: str = "gpt-4.1-nano"

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # Agent config
    max_tool_calls_per_task: int = 5

    # Logging
    log_level: str = "INFO"

    # Storage backend
    storage_backend: str = "redis"

    class Config:
        env_file = str(_ENV_FILE)


settings = Settings()
