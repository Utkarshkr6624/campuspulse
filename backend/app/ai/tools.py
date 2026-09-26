"""Controlled CampusPulse tools for the AI assistant.

Tools always bind to the authenticated student_id from the server.
The LLM cannot supply another student's id.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from typing import Any

from sqlalchemy.orm import Session

from app.services import (
    academic_service,
    analytics_service,
    assignment_service,
    attendance_service,
    course_mark_service,
    document_search_service,
    exam_service,
    student_service,
)


class ToolName(StrEnum):
    GET_STUDENT_PROFILE = "get_student_profile"
    GET_MARKS = "get_marks"
    GET_COURSE_PERFORMANCE = "get_course_performance"
    GET_ATTENDANCE = "get_attendance"
    GET_GPA = "get_gpa"
    GET_CGPA = "get_cgpa"
    GET_EXAMS = "get_exams"
    GET_ASSIGNMENTS = "get_assignments"
    GET_ACADEMIC_INSIGHTS = "get_academic_insights"
    SEARCH_UNIVERSITY_DOCUMENTS = "search_university_documents"


@dataclass(frozen=True)
class ToolResult:
    name: ToolName
    ok: bool
    data: Any
    grounding: str  # PERSONAL_DATA | UNIVERSITY_DOCUMENT | SYSTEM_DATA
    error: str | None = None


@dataclass(frozen=True)
class SourceRef:
    document_id: int
    title: str
    page_number: int | None
    snippet: str
    category: str


class CampusPulseToolContext:
    """Authenticated tool runner. student_id is fixed at construction."""

    def __init__(self, db: Session, student_id: int) -> None:
        self.db = db
        self.student_id = student_id

    def run(self, name: ToolName, *, query: str | None = None) -> ToolResult:
        try:
            if name == ToolName.GET_STUDENT_PROFILE:
                return self._profile()
            if name == ToolName.GET_MARKS:
                return self._marks()
            if name == ToolName.GET_COURSE_PERFORMANCE:
                return self._course_performance()
            if name == ToolName.GET_ATTENDANCE:
                return self._attendance()
            if name == ToolName.GET_GPA:
                return self._gpa()
            if name == ToolName.GET_CGPA:
                return self._cgpa()
            if name == ToolName.GET_EXAMS:
                return self._exams()
            if name == ToolName.GET_ASSIGNMENTS:
                return self._assignments()
            if name == ToolName.GET_ACADEMIC_INSIGHTS:
                return self._insights()
            if name == ToolName.SEARCH_UNIVERSITY_DOCUMENTS:
                return self._search_documents(query or "")
            return ToolResult(name=name, ok=False, data=None, grounding="SYSTEM_DATA", error="Unknown tool.")
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                name=name,
                ok=False,
                data=None,
                grounding="SYSTEM_DATA",
                error=f"Tool failed: {exc}",
            )

    def _profile(self) -> ToolResult:
        student = student_service.get_student(self.db, self.student_id)
        return ToolResult(
            name=ToolName.GET_STUDENT_PROFILE,
            ok=True,
            grounding="PERSONAL_DATA",
            data={
                "full_name": student.full_name,
                "email": student.email,
                "university_id": student.university_id,
            },
        )

    def _marks(self) -> ToolResult:
        overview = course_mark_service.build_overview(self.db, self.student_id)
        return ToolResult(
            name=ToolName.GET_MARKS,
            ok=True,
            grounding="PERSONAL_DATA",
            data=overview.model_dump(mode="json"),
        )

    def _course_performance(self) -> ToolResult:
        courses = academic_service.list_course_performance(self.db, self.student_id)
        return ToolResult(
            name=ToolName.GET_COURSE_PERFORMANCE,
            ok=True,
            grounding="PERSONAL_DATA",
            data=[item.model_dump(mode="json") for item in courses],
        )

    def _attendance(self) -> ToolResult:
        overview = attendance_service.build_overview(self.db, self.student_id)
        return ToolResult(
            name=ToolName.GET_ATTENDANCE,
            ok=True,
            grounding="PERSONAL_DATA",
            data=overview.model_dump(mode="json"),
        )

    def _gpa(self) -> ToolResult:
        gpa = academic_service.get_semester_gpa(self.db, self.student_id)
        return ToolResult(
            name=ToolName.GET_GPA,
            ok=True,
            grounding="PERSONAL_DATA",
            data=gpa.model_dump(mode="json"),
        )

    def _cgpa(self) -> ToolResult:
        cgpa = academic_service.get_cgpa(self.db, self.student_id)
        return ToolResult(
            name=ToolName.GET_CGPA,
            ok=True,
            grounding="PERSONAL_DATA",
            data=cgpa.model_dump(mode="json"),
        )

    def _exams(self) -> ToolResult:
        today = date.today()
        exams = exam_service.list_exams(
            self.db,
            self.student_id,
            upcoming=True,
            date_from=today,
            date_to=today + timedelta(days=14),
        )
        payload = [exam_service.serialize_exam(item).model_dump(mode="json") for item in exams]
        return ToolResult(
            name=ToolName.GET_EXAMS,
            ok=True,
            grounding="PERSONAL_DATA",
            data=payload,
        )

    def _assignments(self) -> ToolResult:
        assignments = assignment_service.list_assignments(
            self.db,
            self.student_id,
            upcoming=True,
        )
        overdue = assignment_service.list_assignments(self.db, self.student_id, completed=False)
        overdue_payload = [
            assignment_service.serialize_assignment(item).model_dump(mode="json")
            for item in overdue
            if assignment_service.serialize_assignment(item).is_overdue
        ]
        upcoming_payload = [
            assignment_service.serialize_assignment(item).model_dump(mode="json") for item in assignments
        ]
        return ToolResult(
            name=ToolName.GET_ASSIGNMENTS,
            ok=True,
            grounding="PERSONAL_DATA",
            data={"upcoming": upcoming_payload, "overdue": overdue_payload},
        )

    def _insights(self) -> ToolResult:
        insights = analytics_service.list_insights(self.db, self.student_id)
        return ToolResult(
            name=ToolName.GET_ACADEMIC_INSIGHTS,
            ok=True,
            grounding="PERSONAL_DATA",
            data=insights.model_dump(mode="json"),
        )

    def _search_documents(self, query: str) -> ToolResult:
        results = document_search_service.search_documents(self.db, query, limit=5)
        return ToolResult(
            name=ToolName.SEARCH_UNIVERSITY_DOCUMENTS,
            ok=True,
            grounding="UNIVERSITY_DOCUMENT",
            data=results.model_dump(mode="json"),
        )


def extract_sources(tool_results: list[ToolResult]) -> list[SourceRef]:
    sources: list[SourceRef] = []
    seen: set[tuple[int, int | None]] = set()
    for result in tool_results:
        if result.name != ToolName.SEARCH_UNIVERSITY_DOCUMENTS or not result.ok:
            continue
        payload = result.data or {}
        for hit in payload.get("results", []):
            key = (hit["document_id"], hit.get("page_number"))
            if key in seen:
                continue
            seen.add(key)
            sources.append(
                SourceRef(
                    document_id=hit["document_id"],
                    title=hit["title"],
                    page_number=hit.get("page_number"),
                    snippet=hit.get("snippet", ""),
                    category=hit.get("category", "GENERAL"),
                )
            )
    return sources
