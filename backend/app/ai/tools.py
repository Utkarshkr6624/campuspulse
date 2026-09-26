"""Controlled CampusPulse tools for the AI assistant.

Tools always bind to the authenticated student_id from the server.
The LLM cannot supply another student's id.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
import re
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
    intelligence_service,
)
from app.schemas.analytics import GpaSimulationCourseInput, GpaSimulationRequest


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
    GET_ACADEMIC_INTELLIGENCE = "get_academic_intelligence"
    SIMULATE_GPA = "simulate_gpa"
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
            if name == ToolName.GET_ACADEMIC_INTELLIGENCE:
                return self._intelligence()
            if name == ToolName.SIMULATE_GPA:
                return self._simulate_gpa(query or "")
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

    def _intelligence(self) -> ToolResult:
        result = intelligence_service.get_academic_intelligence(self.db, self.student_id)
        return ToolResult(
            name=ToolName.GET_ACADEMIC_INTELLIGENCE,
            ok=True,
            grounding="PERSONAL_DATA",
            data=result.model_dump(mode="json"),
        )

    def _simulate_gpa(self, query: str) -> ToolResult:
        from app.services import analytics_service

        performances = academic_service.list_course_performance(self.db, self.student_id)
        lowered = query.lower()
        course_matches = [
            item for item in performances
            if item.course.code.lower() in lowered or item.course.title.lower() in lowered
        ]
        grades = analytics_service.available_letters(self.db)
        grade = next(
            (
                letter
                for letter in grades
                if re.search(
                    rf"(?<![A-Za-z0-9]){re.escape(letter)}(?![A-Za-z0-9])",
                    query,
                    flags=re.IGNORECASE,
                )
            ),
            None,
        )

        target_match = re.search(r"(?:reach|target|at least|goal(?: of)?)\s+(\d+(?:\.\d+)?)", lowered)
        incomplete = [item for item in performances if item.status != "complete"]
        if target_match:
            target = float(target_match.group(1))
            current = academic_service.get_semester_gpa(self.db, self.student_id)
            if current.value is not None and current.value >= target:
                result = {
                    "message": f"Your current semester GPA is {current.value}, which already meets the {target:.2f} target.",
                    "current_gpa": current.model_dump(mode="json"),
                    "projected_gpa": {"value": current.value},
                }
                return ToolResult(name=ToolName.SIMULATE_GPA, ok=True, grounding="PERSONAL_DATA", data=result)
            candidates = []
            for candidate_grade in grades:
                payload = GpaSimulationRequest(courses=[
                    GpaSimulationCourseInput(course_id=item.course.id, letter_grade=candidate_grade)
                    for item in incomplete
                ])
                projected = analytics_service.simulate_gpa(self.db, self.student_id, payload)
                value = projected.projected_gpa.value
                if value is not None and value >= target:
                    candidates.append((candidate_grade, value))
            if candidates:
                answer_grade, value = max(candidates, key=lambda item: grades.index(item[0]))
                result = {
                    "message": (
                        f"If the same grade {answer_grade} is earned in each of {len(incomplete)} "
                        f"currently incomplete course(s), the calculated semester GPA would be {value}. "
                        "This uniform-grade scenario is hypothetical and does not change saved records."
                    ),
                    "current_gpa": current.model_dump(mode="json"),
                    "projected_gpa": {"value": value},
                }
            else:
                result = {
                    "message": (
                        f"The configured grade scale cannot reach {target:.2f} with the current "
                        "course data when one uniform grade is applied to all incomplete courses."
                    ),
                    "current_gpa": current.model_dump(mode="json"),
                    "projected_gpa": {"value": None},
                }
            return ToolResult(name=ToolName.SIMULATE_GPA, ok=True, grounding="PERSONAL_DATA", data=result)

        if len(course_matches) != 1 or grade is None:
            result = {"message": "Name one enrolled course by its exact course code or title and a configured grade (for example, ‘If I get A in CS101’)."}
            return ToolResult(name=ToolName.SIMULATE_GPA, ok=True, grounding="PERSONAL_DATA", data=result)
        performance = course_matches[0]
        if performance.status == "complete":
            result = {"message": f"{performance.course.code} already has a completed result. The current what-if calculator applies hypothetical grades to incomplete courses."}
            return ToolResult(name=ToolName.SIMULATE_GPA, ok=True, grounding="PERSONAL_DATA", data=result)
        simulation = analytics_service.simulate_gpa(
            self.db,
            self.student_id,
            GpaSimulationRequest(courses=[GpaSimulationCourseInput(course_id=performance.course.id, letter_grade=grade)]),
        )
        result = simulation.model_dump(mode="json")
        if "cgpa" in lowered:
            projected_cgpa = analytics_service.project_cgpa_from_semester_scenario(
                self.db, self.student_id, simulation.projected_gpa
            )
            result["current_cgpa"] = academic_service.get_cgpa(self.db, self.student_id).model_dump(mode="json")
            result["projected_cgpa"] = projected_cgpa.model_dump(mode="json")
        return ToolResult(
            name=ToolName.SIMULATE_GPA,
            ok=True,
            grounding="PERSONAL_DATA",
            data=result,
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
