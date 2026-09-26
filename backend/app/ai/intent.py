"""Heuristic intent routing — selects tools without an LLM call."""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.tools import ToolName


@dataclass(frozen=True)
class IntentPlan:
    intents: tuple[str, ...]
    tools: tuple[ToolName, ...]
    needs_llm: bool
    document_query: str | None = None


def plan_tools(message: str) -> IntentPlan:
    text = message.lower()
    tools: list[ToolName] = []
    intents: list[str] = []
    document_query: str | None = None

    personal_keywords = {
        "gpa": ToolName.GET_GPA,
        "cgpa": ToolName.GET_CGPA,
        "grade point": ToolName.GET_GPA,
        "attendance": ToolName.GET_ATTENDANCE,
        "marks": ToolName.GET_MARKS,
        "score": ToolName.GET_COURSE_PERFORMANCE,
        "performance": ToolName.GET_COURSE_PERFORMANCE,
        "subject": ToolName.GET_ACADEMIC_INSIGHTS,
        "insight": ToolName.GET_ACADEMIC_INSIGHTS,
        "attention": ToolName.GET_ACADEMIC_INSIGHTS,
        "weak": ToolName.GET_ACADEMIC_INSIGHTS,
        "exam": ToolName.GET_EXAMS,
        "cat": ToolName.GET_EXAMS,
        "fat": ToolName.GET_EXAMS,
        "assignment": ToolName.GET_ASSIGNMENTS,
        "deadline": ToolName.GET_ASSIGNMENTS,
        "due": ToolName.GET_ASSIGNMENTS,
        "profile": ToolName.GET_STUDENT_PROFILE,
        "my name": ToolName.GET_STUDENT_PROFILE,
    }

    for keyword, tool in personal_keywords.items():
        if keyword in text and tool not in tools:
            tools.append(tool)
            intents.append(keyword)

    policy_signals = (
        "policy",
        "regulation",
        "requirement",
        "rule",
        "circular",
        "handbook",
        "document",
        "according to",
        "university",
        "minimum attendance",
        "explain the",
        "what does the",
        "summarize",
    )
    if any(signal in text for signal in policy_signals):
        tools.append(ToolName.SEARCH_UNIVERSITY_DOCUMENTS)
        intents.append("documents")
        document_query = message.strip()

    # Broad academic summary prompts.
    if any(phrase in text for phrase in ("summarize my", "academic performance", "how am i doing", "overview")):
        for tool in (
            ToolName.GET_GPA,
            ToolName.GET_CGPA,
            ToolName.GET_ATTENDANCE,
            ToolName.GET_ACADEMIC_INSIGHTS,
            ToolName.GET_COURSE_PERFORMANCE,
        ):
            if tool not in tools:
                tools.append(tool)
        intents.append("summary")

    if not tools:
        # Default: light profile + insights so the assistant can still be useful,
        # plus document search for open-ended academic questions.
        tools = [
            ToolName.GET_STUDENT_PROFILE,
            ToolName.GET_ACADEMIC_INSIGHTS,
            ToolName.SEARCH_UNIVERSITY_DOCUMENTS,
        ]
        intents.append("general")
        document_query = message.strip()

    # Deterministic answers when only simple fact tools are needed and phrase is direct.
    simple = set(tools) <= {
        ToolName.GET_GPA,
        ToolName.GET_CGPA,
        ToolName.GET_ATTENDANCE,
        ToolName.GET_EXAMS,
        ToolName.GET_ASSIGNMENTS,
        ToolName.GET_STUDENT_PROFILE,
    }
    direct = any(
        phrase in text
        for phrase in (
            "what is my",
            "what's my",
            "how is my",
            "how are my",
            "when is my",
            "what exams",
            "which exams",
            "what assignments",
        )
    )
    needs_llm = not (simple and direct and ToolName.SEARCH_UNIVERSITY_DOCUMENTS not in tools)

    # Document grounding always benefits from LLM phrasing when a provider is available;
    # orchestrator may still fall back to deterministic formatting.
    if ToolName.SEARCH_UNIVERSITY_DOCUMENTS in tools:
        needs_llm = True

    return IntentPlan(
        intents=tuple(intents),
        tools=tuple(tools),
        needs_llm=needs_llm,
        document_query=document_query,
    )
