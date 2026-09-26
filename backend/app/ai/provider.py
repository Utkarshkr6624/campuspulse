"""LLM provider interface for CampusPulse AI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class AIProviderError(Exception):
    """Raised when the configured LLM provider cannot complete a request."""

    def __init__(self, detail: str = "CampusPulse AI is temporarily unavailable.") -> None:
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class GenerationResult:
    content: str
    model: str | None = None
    provider: str | None = None
    metadata: dict = field(default_factory=dict)


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[ChatMessage],
        temperature: float = 0.2,
    ) -> GenerationResult:
        """Generate an assistant reply. Must not raise raw provider exceptions."""
