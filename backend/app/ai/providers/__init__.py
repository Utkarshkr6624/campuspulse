from app.ai.provider import AIProviderError, LLMProvider
from app.ai.providers.deterministic import DeterministicAcademicProvider
from app.core.config import settings


def get_llm_provider() -> LLMProvider:
    provider = (settings.ai_provider or "deterministic").strip().lower()
    if provider in {"deterministic", "mock", "test", "openai_compatible", "openai", "ollama"}:
        # Phase 11 defaults to a no-network responder. Legacy external-provider settings
        # resolve to the same local provider until an external provider is intentionally
        # implemented and enabled in a future phase.
        return DeterministicAcademicProvider()
    if provider in {"disabled", "off", "none"}:
        raise AIProviderError("CampusPulse AI is temporarily unavailable.")
    return DeterministicAcademicProvider()
