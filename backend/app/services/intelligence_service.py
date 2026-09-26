"""Deterministic academic performance intelligence based on persisted student data."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.analytics_config import (
    ATTENDANCE_HEALTHY_THRESHOLD,
    ATTENDANCE_NEAR_THRESHOLD_MARGIN,
    ATTENDANCE_WARNING_THRESHOLD,
    LOW_SCORE_THRESHOLD,
    STRONG_SCORE_THRESHOLD,
    attendance_health,
)
from app.schemas.analytics import (
    AcademicIntelligence,
    IntelligenceAssessment,
    IntelligenceCourse,
    IntelligenceInsight,
    SemesterComparison,
    SemesterCreditPoint,
    SemesterTrendPoint,
)
from app.services import academic_service, analytics_service, attendance_service, semester_service


def get_academic_intelligence(
    db: Session,
    student_id: int,
    *,
    first_semester_id: int | None = None,
    second_semester_id: int | None = None,
) -> AcademicIntelligence:
    if (first_semester_id is None) != (second_semester_id is None):
        from app.core.exceptions import BadRequestError

        raise BadRequestError("Choose both semesters to compare.")

    semesters = semester_service.list_semesters(db, student_id)
    current = next((item for item in semesters if item.is_current), None)
    previous = next(
        (item for item in reversed(semesters) if item.status == "PREVIOUS"), None
    )
    attendance = attendance_service.build_overview(db, student_id)
    attendance_by_course = {
        item.course.id: item.attendance_percentage for item in attendance.courses
    }

    semester_courses: dict[int, list[dict]] = {}
    trend: list[SemesterTrendPoint] = []
    credits: list[SemesterCreditPoint] = []
    running_quality_points = 0.0
    running_credits = 0
    last_gpa: float | None = None
    for summary in semesters:
        row = semester_service.get_semester(db, student_id, summary.id)
        historical = list(row.history_courses)
        history_codes = {item.course_code for item in historical if item.course_code}
        performances = academic_service.list_course_performance(
            db, student_id, semester_id=row.id
        )
        performances = [item for item in performances if item.course.code not in history_codes]
        rows: list[dict] = []
        for item in historical:
            rows.append({
                "course_id": item.course_id,
                "course_code": item.course_code,
                "course_name": item.course_name,
                "credits": item.credits,
                "status": "complete",
                "score": item.final_score,
                "grade": item.grade or None,
                "grade_point": item.grade_point,
                "assessments": [],
            })
        for item in performances:
            rows.append({
                "course_id": item.course.id,
                "course_code": item.course.code,
                "course_name": item.course.title,
                "credits": item.credits,
                "status": item.status,
                "score": item.final_score,
                "grade": item.grade,
                "grade_point": item.grade_point,
                "assessments": item.assessments,
            })
        semester_courses[row.id] = rows

        completed_credits = sum(
            item["credits"] for item in rows if item["status"] == "complete"
        )
        # Semester GPA uses the same completion and credit rules as Phase 9.
        if summary.gpa.value is not None and summary.gpa.total_credits > 0:
            running_quality_points += summary.gpa.value * summary.gpa.total_credits
            running_credits += summary.gpa.total_credits
        avg_marks = _average([item["score"] for item in rows])
        gpa_change = (
            round(summary.gpa.value - last_gpa, 2)
            if summary.gpa.value is not None and last_gpa is not None
            else None
        )
        if summary.gpa.value is not None:
            last_gpa = summary.gpa.value
        trend.append(SemesterTrendPoint(
            semester_id=row.id,
            semester_number=row.number,
            status=summary.status,
            sgpa=summary.gpa.value,
            cumulative_gpa=round(running_quality_points / running_credits, 2)
            if running_credits else None,
            completed_credits=completed_credits,
            known_credits=sum(item["credits"] for item in rows),
            course_count=len(rows),
            average_marks=avg_marks,
            gpa_change=gpa_change,
        ))
        credits.append(SemesterCreditPoint(
            semester_id=row.id,
            semester_number=row.number,
            known_credits=sum(item["credits"] for item in rows),
            completed_credits=completed_credits,
        ))

    courses: list[IntelligenceCourse] = []
    trend_by_identity: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    all_scores: list[float | None] = []
    completed_courses = 0
    ongoing_courses = 0
    for summary in semesters:
        for item in semester_courses.get(summary.id, []):
            score = item["score"]
            all_scores.append(score)
            if item["status"] == "complete":
                completed_courses += 1
            else:
                ongoing_courses += 1
            # Attendance records have no semester key. Attribute them only to current courses.
            att = (
                attendance_by_course.get(item["course_id"])
                if summary.is_current and item["course_id"] else None
            )
            health = attendance_health(att)
            assessments = [
                IntelligenceAssessment(
                    assessment_type=result.assessment_type,
                    percentage=round(result.normalized_score, 1),
                )
                for result in item["assessments"]
            ]
            by_type = {result.assessment_type: result.percentage for result in assessments}
            cat_delta = (
                round(by_type["CAT2"] - by_type["CAT1"], 1)
                if "CAT1" in by_type and "CAT2" in by_type
                else None
            )
            category = _performance_category(score)
            courses.append(IntelligenceCourse(
                semester_id=summary.id,
                semester_number=summary.number,
                course_id=item["course_id"],
                course_code=item["course_code"],
                course_name=item["course_name"],
                credits=item["credits"],
                status=item["status"],
                score=score,
                grade=item["grade"],
                grade_point=item["grade_point"],
                attendance_percentage=att,
                attendance_health=health,
                performance_category=category,
                assessments=assessments,
                cat1_to_cat2_change=cat_delta,
            ))
            identity = (
                f"code:{item['course_code'].strip().upper()}"
                if item["course_code"]
                else f"id:{item['course_id']}" if item["course_id"] else None
            )
            if identity:
                trend_by_identity[identity].append((summary.number, item))

    course_trends: list[dict] = []
    for identity, rows in trend_by_identity.items():
        ordered = sorted(
            (entry for entry in rows if entry[1]["score"] is not None),
            key=lambda entry: entry[0],
        )
        if len(ordered) < 2:
            continue
        old_number, old = ordered[-2]
        new_number, new = ordered[-1]
        course_trends.append({
            "identity": identity,
            "course_code": new["course_code"] or old["course_code"],
            "course_name": new["course_name"],
            "previous_semester": old_number,
            "current_semester": new_number,
            "previous_score": old["score"],
            "current_score": new["score"],
            "change": round(new["score"] - old["score"], 1),
        })

    current_rows = semester_courses.get(current.id, []) if current else []
    legacy_known_credits = 0
    legacy_completed_credits = 0
    if not semesters:
        legacy_performances = academic_service.list_course_performance(db, student_id)
        current_rows = [{
            "course_id": item.course.id,
            "course_code": item.course.code,
            "course_name": item.course.title,
            "credits": item.credits,
            "status": item.status,
            "score": item.final_score,
            "grade": item.grade,
            "grade_point": item.grade_point,
            "assessments": item.assessments,
        } for item in legacy_performances]
        for item in current_rows:
            completed_courses += int(item["status"] == "complete")
            ongoing_courses += int(item["status"] != "complete")
            legacy_known_credits += item["credits"]
            if item["status"] == "complete":
                legacy_completed_credits += item["credits"]
            all_scores.append(item["score"])
            att = attendance_by_course.get(item["course_id"])
            assessments = [IntelligenceAssessment(
                assessment_type=result.assessment_type,
                percentage=round(result.normalized_score, 1),
            ) for result in item["assessments"]]
            by_type = {result.assessment_type: result.percentage for result in assessments}
            courses.append(IntelligenceCourse(
                semester_id=None, semester_number=None, course_id=item["course_id"],
                course_code=item["course_code"], course_name=item["course_name"],
                credits=item["credits"], status=item["status"], score=item["score"],
                grade=item["grade"], grade_point=item["grade_point"],
                attendance_percentage=att, attendance_health=attendance_health(att),
                performance_category=_performance_category(item["score"]),
                assessments=assessments,
                cat1_to_cat2_change=round(by_type["CAT2"] - by_type["CAT1"], 1)
                if "CAT1" in by_type and "CAT2" in by_type else None,
            ))
    current_credits = sum(item["credits"] for item in current_rows) if current else 0
    current_sgpa = current.gpa.value if current else analytics_service.get_overview(db, student_id).gpa.value
    previous_sgpa = previous.gpa.value if previous else None
    sgpa_change = (
        round(current_sgpa - previous_sgpa, 2)
        if current_sgpa is not None and previous_sgpa is not None else None
    )
    semesters_with_gpa = [item for item in trend if item.sgpa is not None]
    best_semester = max(semesters_with_gpa, key=lambda item: (item.sgpa, -item.semester_number), default=None)
    lowest_semester = min(semesters_with_gpa, key=lambda item: (item.sgpa, item.semester_number), default=None)
    comparison = None
    if first_semester_id is not None and second_semester_id is not None:
        first = semester_service.get_semester(db, student_id, first_semester_id)
        second = semester_service.get_semester(db, student_id, second_semester_id)
        first_summary = next(row for row in semesters if row.id == first.id)
        second_summary = next(row for row in semesters if row.id == second.id)
        first_trend = next(row for row in trend if row.semester_id == first.id)
        second_trend = next(row for row in trend if row.semester_id == second.id)
        comparison = SemesterComparison(
            first_semester_id=first.id,
            first_semester_number=first.number,
            second_semester_id=second.id,
            second_semester_number=second.number,
            sgpa_difference=_difference(first_summary.gpa.value, second_summary.gpa.value),
            average_marks_difference=_difference(first_trend.average_marks, second_trend.average_marks),
            credits_difference=second_trend.known_credits - first_trend.known_credits,
            course_count_difference=second_trend.course_count - first_trend.course_count,
            attendance_difference=None,
            attendance_note="Attendance records are course-wide and do not store a semester, so a semester comparison cannot be calculated.",
        )

    total_completed_credits = sum(item.completed_credits for item in credits) + legacy_completed_credits
    total_known_credits = sum(item.known_credits for item in credits) + legacy_known_credits
    insights = _insights(
        trend, courses, attendance.attendance_percentage,
        completed_credits=total_completed_credits, course_trends=course_trends,
    )
    has_records = bool(semesters or courses or attendance.total_classes)
    if not has_records:
        data_status = "empty"
        message = "Add semester, course, marks, or attendance records to unlock academic intelligence."
    elif len([item for item in trend if item.sgpa is not None]) < 2:
        data_status = "insufficient"
        message = "Add previous semester results to unlock semester performance trends."
    else:
        data_status = "ready"
        message = None

    return AcademicIntelligence(
        data_status=data_status,
        message=message,
        current_sgpa=current_sgpa,
        previous_sgpa=previous_sgpa,
        sgpa_change=sgpa_change,
        best_semester_number=best_semester.semester_number if best_semester else None,
        best_sgpa=best_semester.sgpa if best_semester else None,
        lowest_semester_number=lowest_semester.semester_number if lowest_semester else None,
        lowest_sgpa=lowest_semester.sgpa if lowest_semester else None,
        cgpa=academic_service.get_cgpa(db, student_id),
        completed_credits=total_completed_credits,
        current_semester_credits=current_credits,
        total_known_credits=total_known_credits,
        average_marks=_average(all_scores),
        overall_attendance=attendance.attendance_percentage,
        completed_courses=completed_courses,
        ongoing_courses=ongoing_courses,
        attendance_warning_threshold=ATTENDANCE_WARNING_THRESHOLD,
        attendance_healthy_threshold=ATTENDANCE_HEALTHY_THRESHOLD,
        low_score_threshold=LOW_SCORE_THRESHOLD,
        strong_score_threshold=STRONG_SCORE_THRESHOLD,
        semester_trend=trend,
        credits_by_semester=credits,
        courses=courses,
        course_trends=course_trends,
        insights=insights,
        comparison=comparison,
    )


def _average(values: list[float | None]) -> float | None:
    available = [value for value in values if value is not None]
    return round(sum(available) / len(available), 2) if available else None


def _difference(first: float | None, second: float | None) -> float | None:
    return round(second - first, 2) if first is not None and second is not None else None


def _performance_category(score: float | None) -> str:
    if score is None:
        return "INSUFFICIENT_DATA"
    if score < LOW_SCORE_THRESHOLD:
        return "NEEDS_ATTENTION"
    if score >= STRONG_SCORE_THRESHOLD:
        return "STRONG"
    return "ON_TRACK"


def _insights(trend, courses, overall_attendance, *, completed_credits, course_trends):
    results: list[IntelligenceInsight] = []
    usable_gpas = [item for item in trend if item.sgpa is not None]
    if len(usable_gpas) >= 2:
        change = round(usable_gpas[-1].sgpa - usable_gpas[-2].sgpa, 2)
        direction = "increased" if change > 0 else "decreased" if change < 0 else "was unchanged"
        results.append(IntelligenceInsight(
            type="SEMESTER_GPA_TREND", severity="INFO", title="Semester GPA comparison",
            description=f"SGPA {direction} by {abs(change):.2f} points between the two latest semesters with GPA data.",
            supporting_data={"change": change, "from_semester": usable_gpas[-2].semester_number, "to_semester": usable_gpas[-1].semester_number},
            source_metric="semester SGPA",
        ))
    else:
        results.append(IntelligenceInsight(
            type="INSUFFICIENT_SEMESTER_HISTORY", severity="INFO", title="More semester data needed",
            description="Add previous semester results to calculate an SGPA trend.",
            supporting_data={"semesters_with_gpa": len(usable_gpas)}, source_metric="semester SGPA",
        ))

    for item in courses:
        if item.cat1_to_cat2_change is not None:
            results.append(IntelligenceInsight(
                type="ASSESSMENT_TREND", severity="INFO", title="CAT 1 to CAT 2 change",
                description=f"{item.course_name} changed by {item.cat1_to_cat2_change:+.1f} percentage points from CAT 1 to CAT 2.",
                supporting_data={"change": item.cat1_to_cat2_change, "course_code": item.course_code, "semester": item.semester_number},
                source_metric="normalized CAT assessment percentages",
            ))
        if item.attendance_percentage is not None and item.attendance_percentage < ATTENDANCE_WARNING_THRESHOLD:
            results.append(IntelligenceInsight(
                type="ATTENDANCE_BELOW_THRESHOLD", severity="WARNING", title="Attendance below configured threshold",
                description=f"{item.course_name} attendance is {item.attendance_percentage:.2f}%, below the configured {ATTENDANCE_WARNING_THRESHOLD:.0f}% threshold.",
                supporting_data={"attendance_percentage": item.attendance_percentage, "threshold": ATTENDANCE_WARNING_THRESHOLD, "course_code": item.course_code},
                source_metric="course-wide recorded attendance",
            ))
        elif item.attendance_percentage is not None and item.attendance_percentage < ATTENDANCE_WARNING_THRESHOLD + ATTENDANCE_NEAR_THRESHOLD_MARGIN:
            results.append(IntelligenceInsight(
                type="ATTENDANCE_NEAR_THRESHOLD", severity="INFO", title="Attendance near configured threshold",
                description=f"{item.course_name} attendance is within {ATTENDANCE_NEAR_THRESHOLD_MARGIN:.0f} points above the configured threshold.",
                supporting_data={"attendance_percentage": item.attendance_percentage, "threshold": ATTENDANCE_WARNING_THRESHOLD, "course_code": item.course_code},
                source_metric="course-wide recorded attendance",
            ))
        if item.performance_category == "STRONG":
            results.append(IntelligenceInsight(
                type="STRONG_COURSE_PERFORMANCE", severity="INFO", title="Strong course score",
                description=f"{item.course_name} has a recorded score of {item.score:.1f}%, at or above the configured strong-score threshold.",
                supporting_data={"score": item.score, "threshold": STRONG_SCORE_THRESHOLD, "course_code": item.course_code},
                source_metric="weighted course score",
            ))
        elif item.performance_category == "NEEDS_ATTENTION":
            results.append(IntelligenceInsight(
                type="LOW_COURSE_PERFORMANCE", severity="WARNING", title="Course score below attention threshold",
                description=f"{item.course_name} has a recorded score of {item.score:.1f}%, below the configured attention threshold.",
                supporting_data={"score": item.score, "threshold": LOW_SCORE_THRESHOLD, "course_code": item.course_code},
                source_metric="weighted course score",
            ))
    for item in course_trends:
        results.append(IntelligenceInsight(
            type="COURSE_PERFORMANCE_TREND", severity="INFO", title="Course performance over time",
            description=f"{item['course_code'] or item['course_name']} changed by {item['change']:+.1f} points between semesters {item['previous_semester']} and {item['current_semester']}.",
            supporting_data={"change": item["change"], "previous_score": item["previous_score"], "current_score": item["current_score"]},
            source_metric="matched course code or catalog ID",
        ))
    if overall_attendance is not None:
        results.append(IntelligenceInsight(
            type="OVERALL_ATTENDANCE", severity="INFO", title="Overall attendance recorded",
            description=f"Overall recorded attendance is {overall_attendance:.2f}%.",
            supporting_data={"attendance_percentage": overall_attendance}, source_metric="all recorded attendance",
        ))
    if completed_credits:
        results.append(IntelligenceInsight(
            type="CREDITS_COMPLETED", severity="INFO", title="Completed credit progress",
            description=f"{completed_credits} credits are attached to completed courses in the available records.",
            supporting_data={"completed_credits": completed_credits}, source_metric="completed course credits",
        ))
    return results
