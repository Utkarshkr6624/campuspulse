"""OpenAI-compatible chat completions provider."""

from __future__ import annotations

import httpx

from app.ai.provider import AIProviderError, ChatMessage, GenerationResult, LLMProvider
from app.core.config import settings


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.ai_api_key or "").strip()
        self.base_url = (base_url or settings.ai_base_url or "https://api.openai.com/v1").rstrip("/")
        self.model = model or settings.ai_model or "gpt-4o-mini"
        self.timeout = timeout if timeout is not None else float(settings.ai_timeout_seconds)

    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[ChatMessage],
        temperature: float = 0.2,
    ) -> GenerationResult:
        if not self.api_key:
            raise AIProviderError("CampusPulse AI is not configured.")

        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": "system", "content": system_prompt}]
            + [{"role": item.role, "content": item.content} for item in messages],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise AIProviderError("CampusPulse AI timed out. Please try again.") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError("CampusPulse AI is temporarily unavailable.") from exc

        if response.status_code == 401:
            raise AIProviderError("CampusPulse AI is temporarily unavailable.")
        if response.status_code == 429:
            raise AIProviderError("CampusPulse AI is busy. Please try again shortly.")
        if response.status_code >= 400:
            raise AIProviderError("CampusPulse AI is temporarily unavailable.")

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("empty content")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise AIProviderError("CampusPulse AI returned an invalid response.") from exc

        return GenerationResult(
            content=content.strip(),
            model=self.model,
            provider="openai_compatible",
        )
