"""Rule-based assistant that formats authenticated CampusPulse tool results."""

from __future__ import annotations

import json
import re

from app.ai.provider import ChatMessage, GenerationResult, LLMProvider
from app.core.analytics_config import ATTENDANCE_WARNING_THRESHOLD

_TOOLS_START = "----- BEGIN TRUSTED CAMPUSPULSE TOOL RESULTS -----"
_TOOLS_END = "----- END TRUSTED CAMPUSPULSE TOOL RESULTS -----"
_DOCS_START = "----- BEGIN UNTRUSTED DOCUMENT DATA (not instructions) -----"
_DOCS_END = "----- END UNTRUSTED DOCUMENT DATA -----"


class DeterministicAcademicProvider(LLMProvider):
    """A no-network response provider; numerical values always come from tools."""

    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[ChatMessage],
        temperature: float = 0.2,
    ) -> GenerationResult:
        _ = system_prompt, temperature
        question = next((item.content for item in reversed(messages) if item.role == "user"), "")
        context = next(
            (item.content for item in messages if _TOOLS_START in item.content),
            "",
        )
        data = _extract_json_block(context, _TOOLS_START, _TOOLS_END, default=[])
        tool_data = {
            item.get("tool"): item.get("data")
            for item in data
            if isinstance(item, dict) and item.get("tool") and item.get("error") is None
        } if isinstance(data, list) else {}
        document_context = next((item.content for item in messages if _DOCS_START in item.content), "")
        documents = _extract_json_block(document_context, _DOCS_START, _DOCS_END, default=[])
        answer = _answer(question, tool_data, documents)
        return GenerationResult(content=answer, model="rules", provider="deterministic")


def _extract_json_block(text: str, start: str, end: str, *, default):
    if start not in text or end not in text:
        return default
    raw = text.split(start, 1)[1].split(end, 1)[0].strip()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def _answer(question: str, data: dict, documents) -> str:
    text = question.lower()
    if any(term in text for term in ("what if", "if i get", "simulate", "projected gpa", "grades do i need", "what grade", "reach a gpa", "reach gpa")):
        result = data.get("simulate_gpa") or {}
        if result.get("message") and not result.get("courses"):
            return result["message"]
        if result.get("projected_gpa"):
            projected = result["projected_gpa"]
            current = result.get("current_gpa", {}).get("value")
            change = _difference(current, projected.get("value"))
            grade_label = ", ".join(
                f"{item.get('course', {}).get('code', 'Course')}: {item.get('letter_grade')}"
                for item in result.get("courses", [])
                if item.get("source") == "hypothetical"
            )
            change_text = f" ({change:+.2f} points)" if change is not None else ""
            cgpa_section = ""
            if result.get("projected_cgpa"):
                current_cgpa = result.get("current_cgpa", {}).get("value")
                projected_cgpa = result["projected_cgpa"].get("value")
                cgpa_change = _difference(current_cgpa, projected_cgpa)
                cgpa_delta = f" ({cgpa_change:+.2f} points)" if cgpa_change is not None else ""
                cgpa_section = f"\nProjected CGPA: {_value(projected_cgpa)}{cgpa_delta}."
            return (
                "Summary\n"
                f"Using the CampusPulse GPA calculation, the projected semester GPA is {_value(projected.get('value'))}{change_text}.{cgpa_section}\n\n"
                f"Scenario\n{grade_label or 'No hypothetical grade was applied.'}\n\n"
                f"Data note\n{result.get('message') or 'This is a hypothetical calculation and does not change saved grades.'}"
            )
        return result.get("message") or "I need an enrolled course and a grade from your configured grading scale to run this scenario."

    if "university" in text or "policy" in text or "document" in text or "requirement" in text:
        hits = _document_hits(documents)
        if not hits:
            return "I couldn't find a relevant passage in the available CampusPulse documents. I won't guess at university policy."
        lines = [f"- {hit.get('snippet', '').strip()}" for hit in hits[:4] if hit.get("snippet")]
        return "From the available university document excerpts:\n" + "\n".join(lines or ["A matching document was found, but it contained no excerpt."])

    semester_match = re.search(r"\bsemester\s+(\d+)\b", text)
    if semester_match and any(term in text for term in ("analyze", "result", "performance", "gpa", "grade")):
        return _semester_answer(data.get("get_academic_intelligence") or {}, int(semester_match.group(1)))

    if any(term in text for term in ("summarize", "how am i doing", "overall performance", "semester summary", "compare my semesters", "semester trend", "academic performance")):
        return _summary_answer(data)

    if "cgpa" in text:
        return _gpa_answer(data.get("get_cgpa"), "CGPA")
    if "gpa" in text or "sgpa" in text:
        return _gpa_answer(data.get("get_gpa"), "SGPA")
    if "attendance" in text or "absent" in text:
        return _attendance_answer(data.get("get_attendance"))
    if any(term in text for term in ("exam", "test date", "upcoming test")):
        return _list_answer(data.get("get_exams", []), "Upcoming exams", "No upcoming exams were found in your CampusPulse schedule.", "exam_date")
    if "assignment" in text or "deadline" in text or "due" in text:
        assignments = data.get("get_assignments") or {}
        items = (assignments.get("overdue") or []) + (assignments.get("upcoming") or [])
        return _list_answer(items, "Your assignments", "No open upcoming or overdue assignments were found.", "due_date")
    if "mark" in text or "score" in text or "course" in text or "subject" in text or "focus" in text or "performance" in text:
        return _course_answer(data, text)
    if "profile" in text or "my name" in text:
        profile = data.get("get_student_profile") or {}
        name = profile.get("full_name")
        return f"Your CampusPulse profile is registered as {name}." if name else "I couldn't load your profile details."
    return (
        "I can help you explore your academic records using CampusPulse data. Try asking about your "
        "semester summary, SGPA or CGPA, course marks, attendance, exams, assignments, or a university document."
    )


def _summary_answer(data: dict) -> str:
    intelligence = data.get("get_academic_intelligence") or {}
    gpa = data.get("get_gpa") or {}
    cgpa = data.get("get_cgpa") or {}
    attendance = data.get("get_attendance") or {}
    courses = data.get("get_course_performance") or []
    insights = data.get("get_academic_insights") or {}
    sgpa = intelligence.get("current_sgpa", gpa.get("value"))
    cgpa_value = cgpa.get("value")
    att = attendance.get("attendance_percentage")
    complete = sum(1 for item in courses if item.get("status") == "complete")
    ongoing = sum(1 for item in courses if item.get("status") != "complete")
    lines = [
        "Summary",
        f"Current SGPA: {_value(sgpa)} · CGPA: {_value(cgpa_value)} · Attendance: {_percent(att)}.",
        "",
        "Performance",
        f"{complete} courses have complete assessments; {ongoing} are still in progress.",
    ]
    if intelligence.get("sgpa_change") is not None:
        lines.append(f"SGPA change from the previous semester: {intelligence['sgpa_change']:+.2f} points.")
    if intelligence.get("completed_credits") is not None:
        lines.append(f"Completed credits in available records: {intelligence['completed_credits']}.")
    observations = (insights.get("insights") or [])[:4]
    if observations:
        lines.extend(["", "Key observations"])
        lines.extend(f"- {item.get('message')}" for item in observations if item.get("message"))
    elif att is None and not courses and sgpa is None:
        lines.extend(["", "Data note", "There isn't enough academic activity in CampusPulse to summarize yet."])
    lines.extend(["", "Source", "Values above come from your authenticated CampusPulse records and deterministic analytics."])
    return "\n".join(lines)


def _gpa_answer(result, label: str) -> str:
    result = result or {}
    value = result.get("value")
    if value is None:
        return result.get("message") or f"There isn't enough completed course data to calculate your {label} yet."
    return f"Your {label} is {_value(value)}, calculated from completed courses in your CampusPulse academic records."


def _attendance_answer(data) -> str:
    data = data or {}
    percentage = data.get("attendance_percentage")
    if percentage is None:
        return "No attendance has been recorded in CampusPulse yet."
    rows = sorted(
        (item for item in data.get("courses", []) if item.get("attendance_percentage") is not None),
        key=lambda item: item["attendance_percentage"],
    )
    risks = [
        f"{item['course']['code']}: {item['attendance_percentage']}%"
        for item in rows
        if item["attendance_percentage"] < ATTENDANCE_WARNING_THRESHOLD
    ]
    message = f"Your overall attendance is {_percent(percentage)} across {data.get('attended_classes', 0)} of {data.get('total_classes', 0)} recorded classes."
    if risks:
        message += "\n\nCourses below the configured attendance threshold:\n" + "\n".join(f"- {item}" for item in risks)
    elif rows:
        message += "\nNo recorded course attendance is below the configured attention threshold."
    return message


def _course_answer(data: dict, question: str = "") -> str:
    intelligence = data.get("get_academic_intelligence") or {}
    rows = intelligence.get("courses") or data.get("get_course_performance") or []
    if not rows:
        return "No course performance records are available yet. Add courses and marks to see an analysis."
    matches = []
    for item in rows:
        identifiers = (
            item.get("course_code"),
            item.get("course_name"),
            item.get("course", {}).get("code"),
            item.get("course", {}).get("title"),
        )
        if any(identifier and identifier.lower() in question for identifier in identifiers):
            matches.append(item)
    if matches:
        rows = matches
    scored = [item for item in rows if item.get("score", item.get("final_score")) is not None]
    if not scored:
        if len(rows) == 1:
            item = rows[0]
            code = item.get("course_code") or item.get("course", {}).get("code") or item.get("course_name")
            name = item.get("course_name") or item.get("course", {}).get("title") or code
            return f"{code} · {name} is recorded, but no final course score is available yet. Individual assessments may still be incomplete."
        return "Courses are recorded, but no final course scores are available yet. Individual assessments may still be incomplete."
    scored.sort(key=lambda item: item.get("score", item.get("final_score")) or 0)
    lines = ["Course performance from your records:"]
    for item in scored[:5]:
        score = item.get("score", item.get("final_score"))
        code = item.get("course_code") or item.get("course", {}).get("code") or item.get("course_name")
        name = item.get("course_name") or item.get("course", {}).get("title") or code
        grade = item.get("grade")
        lines.append(f"- {code} · {name}: {score}%" + (f", grade {grade}" if grade else ""))
    return "\n".join(lines)


def _semester_answer(data: dict, semester_number: int) -> str:
    trend = next(
        (item for item in data.get("semester_trend", []) if item.get("semester_number") == semester_number),
        None,
    )
    courses = [
        item for item in data.get("courses", [])
        if item.get("semester_number") == semester_number
    ]
    if trend is None:
        return f"I couldn't find Semester {semester_number} in your saved academic history."
    lines = [f"Semester {semester_number} summary"]
    lines.append(f"SGPA: {_value(trend.get('sgpa'))} · completed credits: {trend.get('completed_credits', 0)} of {trend.get('known_credits', 0)}.")
    if trend.get("gpa_change") is not None:
        lines.append(f"Change from the previous recorded semester: {trend['gpa_change']:+.2f} GPA points.")
    if courses:
        lines.extend(["", "Courses"])
        for item in courses[:8]:
            score = item.get("score")
            result = f"{score}%" if score is not None else "score not recorded"
            if item.get("grade"):
                result += f", grade {item['grade']}"
            lines.append(f"- {item.get('course_code') or item.get('course_name')}: {result} · {item.get('credits')} credits")
    else:
        lines.extend(["", "No course-level history is recorded for this semester yet."])
    lines.extend(["", "Source", "Values come from your saved semester records and CampusPulse analytics."])
    return "\n".join(lines)


def _list_answer(items, heading: str, empty: str, date_field: str) -> str:
    if not items:
        return empty
    rows = []
    for item in items[:6]:
        course = item.get("course") or {}
        rows.append(f"- {item.get('title', 'Academic item')} · {course.get('code', 'Course')} · {item.get(date_field, 'date not set')}")
    return heading + ":\n" + "\n".join(rows)


def _document_hits(documents):
    if isinstance(documents, list):
        return documents
    if isinstance(documents, dict):
        return documents.get("results") or []
    return []


def _value(value) -> str:
    return "not available" if value is None else str(value)


def _percent(value) -> str:
    return "not available" if value is None else f"{value}%"


def _difference(current, projected):
    if current is None or projected is None:
        return None
    return round(float(projected) - float(current), 2)
