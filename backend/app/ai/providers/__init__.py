from app.ai.provider import AIProviderError, LLMProvider
from app.ai.providers.mock import MockLLMProvider
from app.ai.providers.openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


def get_llm_provider() -> LLMProvider:
    provider = (settings.ai_provider or "mock").strip().lower()
    if provider in {"mock", "test"}:
        return MockLLMProvider()
    if provider in {"disabled", "off", "none"}:
        raise AIProviderError("CampusPulse AI is temporarily unavailable.")
    if provider in {"openai_compatible", "openai", "ollama"}:
        return OpenAICompatibleProvider()
    raise AIProviderError("CampusPulse AI is temporarily unavailable.")
