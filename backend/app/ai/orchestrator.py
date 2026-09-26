"""AI orchestrator: intent → tools → grounded response."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.ai.intent import plan_tools
from app.ai.prompts import DOCUMENT_DATA_WRAPPER, SYSTEM_PROMPT, TOOL_RESULTS_WRAPPER
from app.ai.provider import AIProviderError, ChatMessage, LLMProvider
from app.ai.providers import get_llm_provider
from app.ai.tools import CampusPulseToolContext, SourceRef, ToolName, ToolResult, extract_sources
from app.core.config import settings


@dataclass
class OrchestratorResult:
    answer: str
    sources: list[SourceRef] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    grounding: list[str] = field(default_factory=list)
    provider: str | None = None


class ChatOrchestrator:
    def __init__(self, db: Session, student_id: int, provider: LLMProvider | None = None) -> None:
        self.db = db
        self.student_id = student_id
        self.provider = provider
        self.tools = CampusPulseToolContext(db, student_id)

    def handle(self, message: str, history: list[ChatMessage] | None = None) -> OrchestratorResult:
        cleaned = " ".join(message.split()).strip()
        if not cleaned:
            return OrchestratorResult(answer="Please ask a question about your academics or university documents.")

        # Prompt-injection style requests for other students are refused at the tool boundary
        # and called out here when explicit.
        lowered = cleaned.lower()
        if any(
            phrase in lowered
            for phrase in (
                "another student",
                "other student's",
                "student id ",
                "show me all students",
                "ignore your instructions",
                "ignore previous instructions",
            )
        ) and any(word in lowered for word in ("marks", "gpa", "attendance", "data", "records")):
            if "ignore" in lowered:
                return OrchestratorResult(
                    answer=(
                        "I can't follow instructions that try to override CampusPulse security rules. "
                        "I only use your authenticated account data and approved university documents."
                    ),
                    grounding=["SYSTEM_DATA"],
                )

        plan = plan_tools(cleaned)
        results: list[ToolResult] = []
        for tool in plan.tools:
            query = (
                plan.document_query
                if tool == ToolName.SEARCH_UNIVERSITY_DOCUMENTS
                else cleaned if tool == ToolName.SIMULATE_GPA else None
            )
            results.append(self.tools.run(tool, query=query))

        sources = extract_sources(results)
        grounding = sorted({item.grounding for item in results if item.ok})
        tools_used = [item.name.value for item in results]

        # Deterministic short-circuit for simple personal facts when possible.
        direct = _try_direct_answer(cleaned, results)
        if direct and not plan.needs_llm:
            return OrchestratorResult(
                answer=direct,
                sources=sources,
                tools_used=tools_used,
                grounding=grounding or ["PERSONAL_DATA"],
                provider="deterministic",
            )

        provider = self.provider
        try:
            if provider is None:
                provider = get_llm_provider()
        except AIProviderError:
            fallback = direct or _format_fallback_answer(results, sources)
            return OrchestratorResult(
                answer=fallback,
                sources=sources,
                tools_used=tools_used,
                grounding=grounding or ["SYSTEM_DATA"],
                provider="fallback",
            )

        context_message = _build_context_message(results, sources)
        history_messages = _trim_history(history or [], settings.ai_max_history_messages)
        messages = [
            *history_messages,
            ChatMessage(role="user", content=context_message),
            ChatMessage(role="user", content=cleaned),
        ]
        try:
            generation = provider.generate(system_prompt=SYSTEM_PROMPT, messages=messages)
            answer = generation.content
            provider_name = generation.provider
        except AIProviderError:
            answer = direct or _format_fallback_answer(results, sources)
            provider_name = "fallback"

        return OrchestratorResult(
            answer=answer,
            sources=sources,
            tools_used=tools_used,
            grounding=grounding or ["SYSTEM_DATA"],
            provider=provider_name,
        )


def _trim_history(history: list[ChatMessage], limit: int) -> list[ChatMessage]:
    if limit <= 0:
        return []
    return history[-limit:]


def _build_context_message(results: list[ToolResult], sources: list[SourceRef]) -> str:
    tool_payload = []
    doc_bits = []
    for result in results:
        if not result.ok:
            tool_payload.append({"tool": result.name.value, "error": result.error})
            continue
        if result.name == ToolName.SEARCH_UNIVERSITY_DOCUMENTS:
            doc_bits.append(json.dumps(_bound_context(result.data), default=str))
        else:
            tool_payload.append({"tool": result.name.value, "data": _bound_context(result.data)})
    parts = [
        TOOL_RESULTS_WRAPPER.format(content=json.dumps(tool_payload, default=str)),
    ]
    if doc_bits:
        parts.append(DOCUMENT_DATA_WRAPPER.format(content="\n\n".join(doc_bits)))
    if sources:
        parts.append(
            "Available citation candidates: "
            + json.dumps(
                [
                    {
                        "document_id": item.document_id,
                        "title": item.title,
                        "page_number": item.page_number,
                    }
                    for item in sources
                ]
            )
        )
    return "\n".join(parts)


def _bound_context(value, depth: int = 0):
    """Keep tool context useful and bounded without truncating its JSON structure."""
    if depth >= 6:
        return "…"
    if isinstance(value, dict):
        return {
            str(key): _bound_context(item, depth + 1)
            for key, item in list(value.items())[:40]
        }
    if isinstance(value, list):
        return [_bound_context(item, depth + 1) for item in value[:20]]
    if isinstance(value, str) and len(value) > 1600:
        return value[:1600] + "…"
    return value


def _try_direct_answer(message: str, results: list[ToolResult]) -> str | None:
    text = message.lower()
    by_name = {item.name: item for item in results if item.ok}

    if "gpa" in text and "cgpa" not in text and ToolName.GET_GPA in by_name:
        data = by_name[ToolName.GET_GPA].data or {}
        value = data.get("value")
        if value is None:
            return data.get("message") or "I don't have enough assessment data to calculate your GPA yet."
        return f"Your current GPA is {value}, based on completed course assessments in CampusPulse."

    if "cgpa" in text and ToolName.GET_CGPA in by_name:
        data = by_name[ToolName.GET_CGPA].data or {}
        value = data.get("value")
        if value is None:
            return data.get("message") or "I don't have enough assessment data to calculate your CGPA yet."
        return f"Your CGPA is {value}, based on completed courses in CampusPulse."

    if "attendance" in text and ToolName.GET_ATTENDANCE in by_name and "policy" not in text and "requirement" not in text:
        data = by_name[ToolName.GET_ATTENDANCE].data or {}
        percentage = data.get("attendance_percentage")
        if percentage is None:
            return "No attendance has been recorded in CampusPulse yet."
        return (
            f"Your overall attendance is currently {percentage}%, "
            f"based on {data.get('attended_classes', 0)}/{data.get('total_classes', 0)} classes recorded in CampusPulse."
        )

    if "exam" in text and ToolName.GET_EXAMS in by_name:
        exams = by_name[ToolName.GET_EXAMS].data or []
        if not exams:
            return "I don't have upcoming exams on your CampusPulse schedule for the next two weeks."
        lines = [
            f"- {item['course']['title']} — {item['title']} on {item['exam_date']}"
            for item in exams[:5]
        ]
        return "Here are your upcoming exams from CampusPulse:\n" + "\n".join(lines)

    if ("assignment" in text or "due" in text) and ToolName.GET_ASSIGNMENTS in by_name:
        data = by_name[ToolName.GET_ASSIGNMENTS].data or {}
        upcoming = data.get("upcoming") or []
        overdue = data.get("overdue") or []
        if not upcoming and not overdue:
            return "You have no open upcoming assignments in CampusPulse right now."
        parts = []
        if overdue:
            parts.append(
                "Overdue:\n"
                + "\n".join(f"- {item['title']} ({item['course']['code']}) due {item['due_date']}" for item in overdue[:5])
            )
        if upcoming:
            parts.append(
                "Upcoming:\n"
                + "\n".join(f"- {item['title']} ({item['course']['code']}) due {item['due_date']}" for item in upcoming[:5])
            )
        return "Based on your CampusPulse assignments:\n" + "\n".join(parts)

    return None


def _format_fallback_answer(results: list[ToolResult], sources: list[SourceRef]) -> str:
    direct = None
    for result in results:
        sample = _try_direct_answer(result.name.value.replace("_", " "), [result])
        if sample:
            direct = sample
            break
    if sources:
        citations = "; ".join(
            f"{item.title}" + (f" p.{item.page_number}" if item.page_number else "") for item in sources[:3]
        )
        base = direct or "I found related university document excerpts."
        return f"{base}\n\nSources: {citations}"
    if direct:
        return direct
    failures = [item.error for item in results if not item.ok and item.error]
    if failures:
        return "CampusPulse AI could not complete that request with the available academic data."
    return (
        "I couldn't find enough CampusPulse data or university documents to answer that confidently. "
        "Try asking about your GPA, attendance, exams, assignments, or a specific policy."
    )
