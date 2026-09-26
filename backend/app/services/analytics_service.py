"""Academic analytics orchestration.

Reuses academic, attendance, exam, and assignment services. Does not
reimplement GPA, score, or attendance math.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from app.core.analytics_config import (
    LOW_SCORE_THRESHOLD,
    PERFORMANCE_MEANINGFUL_DELTA,
    UPCOMING_EXAM_DAYS,
    AttendanceHealth,
    InsightSeverity,
    InsightType,
    attendance_health,
)
from app.core.assessment_types import ASSESSMENT_TYPE_LABELS, AssessmentType
from app.core.exceptions import BadRequestError
from app.schemas.academic import CoursePerformance, GpaRead
from app.schemas.analytics import (
    AcademicInsight,
    AnalyticsOverview,
    AttendanceAnalytics,
    AttendanceCourseAnalytics,
    AttentionCourse,
    CourseAnalytics,
    GradeDistributionBucket,
    GpaSimulationCourseResult,
    GpaSimulationRequest,
    GpaSimulationResponse,
    InsightsResponse,
    PerformancePoint,
    PerformanceTrend,
)
from app.services import (
    academic_service,
    assignment_service,
    attendance_service,
    course_mark_service,
    course_service,
    exam_service,
    grading_scheme_service,
)
from app.services.academic import GradedCourseInput, compute_gpa, letter_to_grade_point
from app.services.academic.grades import GradeBandRule
from app.services.academic.percentages import assessment_percentage

_ASSESSMENT_ORDER = {
    AssessmentType.CAT1.value: 1,
    AssessmentType.CAT2.value: 2,
    AssessmentType.INTERNAL.value: 3,
    AssessmentType.LAB.value: 4,
    AssessmentType.ASSIGNMENT.value: 5,
    AssessmentType.FAT.value: 6,
    AssessmentType.OTHER.value: 7,
}


def get_overview(db: Session, student_id: int) -> AnalyticsOverview:
    courses = academic_service.list_course_performance(db, student_id)
    summary = academic_service.get_summary(db, student_id)
    attendance = attendance_service.build_overview(db, student_id)
    attendance_by_course = {
        item.course.id: item.attendance_percentage for item in attendance.courses
    }
    letters = available_letters(db)

    total_credits = sum(item.credits for item in courses)
    completed_credits = sum(item.credits for item in courses if item.status == "complete")

    if not courses:
        return AnalyticsOverview(
            gpa=summary.gpa,
            cgpa=summary.cgpa,
            total_courses=0,
            completed_courses=0,
            incomplete_courses=0,
            total_credits=0,
            completed_credits=0,
            overall_attendance=attendance.attendance_percentage,
            grade_distribution=[],
            courses_requiring_attention=[],
            available_grade_letters=letters,
            data_status="empty",
            message="Enroll in courses and add marks or attendance to unlock analytics.",
        )

    return AnalyticsOverview(
        gpa=summary.gpa,
        cgpa=summary.cgpa,
        total_courses=summary.enrolled_courses,
        completed_courses=summary.completed_courses,
        incomplete_courses=summary.incomplete_courses,
        total_credits=total_credits,
        completed_credits=completed_credits,
        overall_attendance=attendance.attendance_percentage,
        grade_distribution=_grade_distribution(db, courses),
        courses_requiring_attention=_attention_courses(courses, attendance_by_course),
        available_grade_letters=letters,
        data_status="ready",
        message=None,
    )


def list_course_analytics(db: Session, student_id: int) -> list[CourseAnalytics]:
    courses = academic_service.list_course_performance(db, student_id)
    attendance = attendance_service.build_overview(db, student_id)
    attendance_by_course = {item.course.id: item for item in attendance.courses}

    results: list[CourseAnalytics] = []
    for item in courses:
        course = course_service.get_course(db, item.course.id, student_id)
        scheme = grading_scheme_service.resolve_scheme_for_course(db, course.grading_scheme_id)
        required = sum(1 for weight in scheme.weights if weight.weight_percent > 0)
        att = attendance_by_course.get(item.course.id)
        percentage = att.attendance_percentage if att else None
        results.append(
            CourseAnalytics(
                course=item.course,
                semester=item.semester,
                credits=item.credits,
                status=item.status,
                current_score=item.final_score,
                grade=item.grade,
                grade_point=item.grade_point,
                completed_assessments=len(item.assessments),
                required_assessments=required,
                missing_assessments=item.missing_assessment_types,
                attendance_percentage=percentage,
                attendance_health=attendance_health(percentage),
                message=item.message,
            )
        )
    results.sort(key=lambda row: (-(row.current_score or -1.0), row.course.code))
    return results


def get_performance_trend(db: Session, student_id: int) -> PerformanceTrend:
    marks = course_mark_service.list_marks(db, student_id)
    if not marks:
        return PerformanceTrend(
            status="empty",
            points=[],
            message="Add assessment marks to see a performance trend.",
        )

    raw_points: list[tuple[date | None, int, int, PerformancePoint]] = []
    for mark in marks:
        percentage = assessment_percentage(mark.marks_obtained, mark.maximum_marks)
        try:
            label = ASSESSMENT_TYPE_LABELS.get(
                mark.assessment_type,
                mark.assessment_type.replace("_", " ").title(),
            )
        except ValueError:
            label = mark.assessment_type
        point = PerformancePoint(
            assessment_name=label,
            assessment_type=mark.assessment_type,
            assessment_date=mark.assessment_date.isoformat() if mark.assessment_date else None,
            percentage=round(percentage, 1),
            course=mark.course,
        )
        raw_points.append(
            (
                mark.assessment_date,
                _ASSESSMENT_ORDER.get(mark.assessment_type, 99),
                mark.id,
                point,
            )
        )

    raw_points.sort(
        key=lambda item: (
            item[0] is None,
            item[0] or date.min,
            item[1],
            item[2],
        )
    )
    points = [item[3] for item in raw_points]
    if len(points) < 2:
        return PerformanceTrend(
            status="insufficient",
            points=points,
            message="At least two assessment results are needed to show a performance trend.",
        )

    enriched: list[PerformancePoint] = []
    previous: float | None = None
    for point in points:
        change = None if previous is None else round(point.percentage - previous, 1)
        enriched.append(point.model_copy(update={"change_from_previous": change}))
        previous = point.percentage

    return PerformanceTrend(status="ready", points=enriched, message=None)


def get_attendance_analytics(db: Session, student_id: int) -> AttendanceAnalytics:
    overview = attendance_service.build_overview(db, student_id)
    overall = overview.attendance_percentage
    overall_health = attendance_health(overall)
    if overview.total_classes == 0:
        overall_message = "No attendance has been recorded yet."
    else:
        overall_message = f"Overall attendance is currently {overall}%."

    courses: list[AttendanceCourseAnalytics] = []
    for item in overview.courses:
        health = attendance_health(item.attendance_percentage)
        if item.attendance_percentage is None:
            message = "No attendance recorded for this course."
        else:
            message = f"Attendance is currently {item.attendance_percentage}%."
        courses.append(
            AttendanceCourseAnalytics(
                course=item.course,
                attended=item.attended_classes,
                total=item.total_classes,
                missed=item.missed_classes,
                percentage=item.attendance_percentage,
                health=health,
                message=message,
            )
        )

    return AttendanceAnalytics(
        overall_percentage=overall,
        overall_health=overall_health,
        overall_message=overall_message,
        courses=courses,
    )


def list_insights(db: Session, student_id: int) -> InsightsResponse:
    courses = academic_service.list_course_performance(db, student_id)
    attendance = get_attendance_analytics(db, student_id)
    trend = get_performance_trend(db, student_id)
    exams = exam_service.list_exams(db, student_id, upcoming=True)
    assignments = assignment_service.list_assignments(db, student_id)

    insights: list[AcademicInsight] = []

    for item in attendance.courses:
        if item.health in {AttendanceHealth.WARNING, AttendanceHealth.CRITICAL} and item.percentage is not None:
            severity = (
                InsightSeverity.CRITICAL
                if item.health == AttendanceHealth.CRITICAL
                else InsightSeverity.WARNING
            )
            insights.append(
                AcademicInsight(
                    id=f"attendance-{item.course.id}",
                    type=InsightType.LOW_ATTENDANCE,
                    severity=severity,
                    title="Attendance needs attention",
                    message=f"{item.course.title} attendance is currently {item.percentage}%.",
                    course_id=item.course.id,
                    course_code=item.course.code,
                    supporting_value=item.percentage,
                    navigation_target="/attendance",
                )
            )

    for item in courses:
        if item.status == "complete" and item.final_score is not None and item.final_score < LOW_SCORE_THRESHOLD:
            insights.append(
                AcademicInsight(
                    id=f"score-{item.course.id}",
                    type=InsightType.LOW_SCORE,
                    severity=InsightSeverity.WARNING,
                    title="Course score is below attention threshold",
                    message=(
                        f"{item.course.title} currently scores {item.final_score}% "
                        f"(below {LOW_SCORE_THRESHOLD}%)."
                    ),
                    course_id=item.course.id,
                    course_code=item.course.code,
                    supporting_value=item.final_score,
                    navigation_target="/marks",
                )
            )
        if item.missing_assessment_types:
            insights.append(
                AcademicInsight(
                    id=f"missing-{item.course.id}",
                    type=InsightType.MISSING_ASSESSMENT,
                    severity=InsightSeverity.INFO,
                    title="Assessments still missing",
                    message=(
                        f"{item.course.title} is missing "
                        f"{len(item.missing_assessment_types)} required assessment"
                        f"{'' if len(item.missing_assessment_types) == 1 else 's'}."
                    ),
                    course_id=item.course.id,
                    course_code=item.course.code,
                    supporting_value=len(item.missing_assessment_types),
                    navigation_target="/marks",
                )
            )

    if trend.status == "ready" and len(trend.points) >= 2:
        last = trend.points[-1]
        if last.change_from_previous is not None and abs(last.change_from_previous) >= PERFORMANCE_MEANINGFUL_DELTA:
            improved = last.change_from_previous > 0
            insights.append(
                AcademicInsight(
                    id="performance-delta",
                    type=(
                        InsightType.PERFORMANCE_IMPROVEMENT
                        if improved
                        else InsightType.PERFORMANCE_DECLINE
                    ),
                    severity=InsightSeverity.INFO,
                    title="Recent assessment change",
                    message=(
                        f"{last.assessment_name} in {last.course.title} changed by "
                        f"{last.change_from_previous:+.1f} percentage points versus the previous assessment."
                    ),
                    course_id=last.course.id,
                    course_code=last.course.code,
                    supporting_value=last.change_from_previous,
                    navigation_target="/analytics",
                )
            )

    for exam in exams:
        serialized = exam_service.serialize_exam(exam)
        if 0 <= serialized.days_until <= UPCOMING_EXAM_DAYS:
            day_label = "day" if serialized.days_until == 1 else "days"
            insights.append(
                AcademicInsight(
                    id=f"exam-{exam.id}",
                    type=InsightType.UPCOMING_EXAM,
                    severity=InsightSeverity.INFO,
                    title="Upcoming exam",
                    message=(
                        f"{exam.course.title} has an upcoming exam in "
                        f"{serialized.days_until} {day_label}."
                    ),
                    course_id=exam.course_id,
                    course_code=exam.course.code,
                    supporting_value=serialized.days_until,
                    navigation_target="/exams",
                )
            )

    for assignment in assignments:
        serialized = assignment_service.serialize_assignment(assignment)
        if serialized.is_overdue:
            insights.append(
                AcademicInsight(
                    id=f"assignment-{assignment.id}",
                    type=InsightType.OVERDUE_ASSIGNMENT,
                    severity=InsightSeverity.WARNING,
                    title="Overdue assignment",
                    message=f"{assignment.title} for {assignment.course.code} is overdue.",
                    course_id=assignment.course_id,
                    course_code=assignment.course.code,
                    supporting_value=serialized.days_until,
                    navigation_target="/assignments",
                )
            )

    severity_rank = {
        InsightSeverity.CRITICAL: 0,
        InsightSeverity.WARNING: 1,
        InsightSeverity.INFO: 2,
    }
    insights.sort(key=lambda item: (severity_rank[item.severity], item.title))

    if not insights:
        return InsightsResponse(
            insights=[],
            status="empty",
            message="No notable academic insights yet. Add more marks, attendance, or deadlines.",
        )
    return InsightsResponse(insights=insights, status="ready", message=None)


def simulate_gpa(db: Session, student_id: int, payload: GpaSimulationRequest) -> GpaSimulationResponse:
    performances = academic_service.list_course_performance(db, student_id)
    current = academic_service.get_semester_gpa(db, student_id)
    if not performances:
        return GpaSimulationResponse(
            current_gpa=current,
            projected_gpa=current,
            courses=[],
            message="Enroll in courses before running a GPA simulation.",
        )

    hypo_by_course = {item.course_id: item.letter_grade.strip().upper() for item in payload.courses}
    default_scheme = grading_scheme_service.get_default_scheme(db)
    default_bands = _band_rules(default_scheme.grade_bands)

    graded: list[GradedCourseInput] = []
    results: list[GpaSimulationCourseResult] = []

    for performance in performances:
        course = course_service.get_course(db, performance.course.id, student_id)
        scheme = grading_scheme_service.resolve_scheme_for_course(db, course.grading_scheme_id)
        bands = _band_rules(scheme.grade_bands) or default_bands

        if performance.status == "complete" and performance.grade_point is not None:
            graded.append(
                GradedCourseInput(
                    course_id=performance.course.id,
                    credits=performance.credits,
                    grade_point=performance.grade_point,
                    status="complete",
                )
            )
            results.append(
                GpaSimulationCourseResult(
                    course=performance.course,
                    credits=performance.credits,
                    source="actual",
                    letter_grade=performance.grade,
                    grade_point=performance.grade_point,
                )
            )
            continue

        letter = hypo_by_course.get(performance.course.id)
        if letter is None:
            results.append(
                GpaSimulationCourseResult(
                    course=performance.course,
                    credits=performance.credits,
                    source="omitted",
                    letter_grade=None,
                    grade_point=None,
                )
            )
            continue

        try:
            grade_point = letter_to_grade_point(letter, bands)
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc

        graded.append(
            GradedCourseInput(
                course_id=performance.course.id,
                credits=performance.credits,
                grade_point=grade_point,
                status="complete",
            )
        )
        results.append(
            GpaSimulationCourseResult(
                course=performance.course,
                credits=performance.credits,
                source="hypothetical",
                letter_grade=letter,
                grade_point=grade_point,
            )
        )

    projected = compute_gpa(graded)
    projected_read = GpaRead(
        status=projected.status,
        value=projected.value,
        credited_courses=projected.credited_courses,
        total_credits=projected.total_credits,
        semester=None,
        message=projected.message,
    )
    return GpaSimulationResponse(
        current_gpa=current,
        projected_gpa=projected_read,
        courses=results,
        message=(
            None
            if projected.status == "complete"
            else projected.message or "Provide hypothetical grades for incomplete courses."
        ),
    )


def project_cgpa_from_semester_scenario(
    db: Session, student_id: int, projected_semester_gpa: GpaRead
) -> GpaRead:
    """Combine prior credits with a simulated current-semester result via the GPA engine."""
    existing = academic_service.get_cgpa(db, student_id)
    current = academic_service.get_semester_gpa(db, student_id)
    prior_credits = max(0, existing.total_credits - current.total_credits)
    inputs: list[GradedCourseInput] = []

    if prior_credits and existing.value is not None:
        prior_quality_points = existing.value * existing.total_credits
        if current.value is not None:
            prior_quality_points -= current.value * current.total_credits
        inputs.append(GradedCourseInput(
            course_id=-1,
            credits=prior_credits,
            grade_point=prior_quality_points / prior_credits,
            status="complete",
        ))

    if projected_semester_gpa.value is not None and projected_semester_gpa.total_credits:
        inputs.append(GradedCourseInput(
            course_id=-2,
            credits=projected_semester_gpa.total_credits,
            grade_point=projected_semester_gpa.value,
            status="complete",
        ))

    result = compute_gpa(inputs)
    return GpaRead(
        status=result.status,
        value=result.value,
        credited_courses=result.credited_courses,
        total_credits=result.total_credits,
        semester=None,
        message=result.message,
    )


def available_letters(db: Session) -> list[str]:
    scheme = grading_scheme_service.get_default_scheme(db)
    ordered = sorted(scheme.grade_bands, key=lambda band: band.min_score, reverse=True)
    return [band.letter for band in ordered]


def _grade_distribution(db: Session, courses: list[CoursePerformance]) -> list[GradeDistributionBucket]:
    completed = [item for item in courses if item.status == "complete" and item.grade]
    if not completed:
        return []
    scheme = grading_scheme_service.get_default_scheme(db)
    ordered_letters = [
        band.letter for band in sorted(scheme.grade_bands, key=lambda band: band.min_score, reverse=True)
    ]
    counts = Counter(item.grade for item in completed)
    buckets = [
        GradeDistributionBucket(letter=letter, count=counts.get(letter, 0)) for letter in ordered_letters
    ]
    for letter, count in counts.items():
        if letter not in ordered_letters:
            buckets.append(GradeDistributionBucket(letter=letter, count=count))
    return buckets


def _attention_courses(
    courses: list[CoursePerformance],
    attendance_by_course: dict[int, float | None],
) -> list[AttentionCourse]:
    attention: list[AttentionCourse] = []
    for item in courses:
        reasons: list[str] = []
        percentage = attendance_by_course.get(item.course.id)
        health = attendance_health(percentage)
        if health in {AttendanceHealth.WARNING, AttendanceHealth.CRITICAL} and percentage is not None:
            reasons.append(f"Attendance {percentage}%")
        if item.missing_assessment_types:
            reasons.append(f"{len(item.missing_assessment_types)} missing assessment(s)")
        if item.status == "complete" and item.final_score is not None and item.final_score < LOW_SCORE_THRESHOLD:
            reasons.append(f"Score {item.final_score}%")
        if reasons:
            attention.append(AttentionCourse(course=item.course, reasons=reasons))
    return attention


def _band_rules(bands) -> list[GradeBandRule]:
    return [
        GradeBandRule(
            letter=band.letter,
            min_score=band.min_score,
            max_score=band.max_score,
            grade_point=band.grade_point,
        )
        for band in bands
    ]
