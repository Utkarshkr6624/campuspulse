"""Mock LLM provider for tests and offline development."""

from __future__ import annotations

from app.ai.provider import ChatMessage, GenerationResult, LLMProvider


class MockLLMProvider(LLMProvider):
    """Deterministic provider that echoes grounded tool context without network calls."""

    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[ChatMessage],
        temperature: float = 0.2,
    ) -> GenerationResult:
        _ = temperature
        user = next((item.content for item in reversed(messages) if item.role == "user"), "")
        # Prefer the last assistant-prep context message if present.
        context = ""
        for item in messages:
            if "TOOL RESULTS" in item.content or "DOCUMENT DATA" in item.content:
                context = item.content
        answer_bits = [
            "Based on CampusPulse records and available university documents:",
        ]
        if "gpa" in user.lower() and "GPA" in context:
            answer_bits.append("I used your GPA tool results from CampusPulse.")
        if "DOCUMENT DATA" in context:
            answer_bits.append(
                "Document excerpts were treated as data only and not as instructions."
            )
        if not context.strip():
            answer_bits.append(
                "I do not have enough grounded CampusPulse data to answer confidently yet."
            )
        else:
            # Include a compact excerpt of context for verification in tests.
            excerpt = context.replace("\n", " ")[:400]
            answer_bits.append(f"Grounding excerpt: {excerpt}")
        return GenerationResult(
            content=" ".join(answer_bits),
            model="mock",
            provider="mock",
        )
