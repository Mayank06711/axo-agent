import logging

from backend.config import settings
from backend.services.llm.base import LLMProvider

logger = logging.getLogger("axo_agent.llm")


def _is_configured(provider: str) -> bool:
    """Check if a provider has valid credentials set in environment."""
    checks = {
        "openai": lambda: bool(settings.openai_api_key),
        "azure": lambda: bool(settings.azure_openai_api_key and settings.azure_openai_endpoint),
        "anthropic": lambda: bool(settings.anthropic_api_key),
        "google": lambda: bool(settings.google_api_key),
    }
    checker = checks.get(provider)
    return checker() if checker else False


def get_available_providers() -> list[str]:
    """Return providers that have credentials configured in the environment."""
    return [p for p in ("openai", "azure", "anthropic", "google") if _is_configured(p)]


def resolve_provider_and_model(
    provider: str | None, model: str | None
) -> tuple[str, str]:
    """Resolve provider/model from request or fall back to config defaults.
    Validates that the resolved provider is actually configured."""
    resolved_provider = provider or settings.default_llm_provider
    resolved_model = model or settings.default_llm_model

    available = get_available_providers()
    if not available:
        raise ValueError(
            "No LLM provider configured. Set at least one API key in .env "
            "(OPENAI_API_KEY, AZURE_OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)"
        )

    if resolved_provider not in available:
        raise ValueError(
            f"Provider '{resolved_provider}' is not configured. "
            f"Available providers: {', '.join(available)}"
        )

    return resolved_provider, resolved_model


def get_llm(provider: str | None = None, model: str | None = None) -> LLMProvider:
    """Factory: returns a LangChain chat model. Resolves defaults from config."""
    provider, model = resolve_provider_and_model(provider, model)
    logger.info("creating LLM | provider=%s model=%s", provider, model)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, api_key=settings.openai_api_key)

    if provider == "azure":
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_deployment=model or settings.azure_openai_deployment,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_version,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, api_key=settings.anthropic_api_key)

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model, google_api_key=settings.google_api_key
        )

    raise ValueError(f"Unsupported provider: '{provider}'")
