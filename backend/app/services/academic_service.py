from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.course_mark import CourseMark
from app.models.enrollment import Enrollment
from app.schemas.academic import (
    AcademicSummary,
    AssessmentPerformance,
    CoursePerformance,
    GpaRead,
)
from app.services import grading_scheme_service
from app.services.academic import (
    GradeBandRule,
    GradedCourseInput,
    WeightedAssessmentInput,
    compute_cgpa,
    compute_course_score,
    compute_gpa,
    compute_grade,
)


def list_course_performance(db: Session, student_id: int) -> list[CoursePerformance]:
    enrollments = _active_enrollments(db, student_id)
    marks_by_course = _marks_by_course(db, student_id)
    results: list[CoursePerformance] = []
    for enrollment in enrollments:
        results.append(_build_course_performance(db, enrollment, marks_by_course.get(enrollment.course_id, [])))
    results.sort(key=lambda item: item.course.code)
    return results


def get_semester_gpa(db: Session, student_id: int, semester: str | None = None) -> GpaRead:
    performances = list_course_performance(db, student_id)
    if semester is not None:
        performances = [item for item in performances if item.semester == semester]
    graded = [_to_graded_input(item) for item in performances]
    result = compute_gpa(graded)
    return GpaRead(
        status=result.status,
        value=result.value,
        credited_courses=result.credited_courses,
        total_credits=result.total_credits,
        semester=semester,
        message=result.message,
    )


def get_cgpa(db: Session, student_id: int) -> GpaRead:
    performances = list_course_performance(db, student_id)
    graded = [_to_graded_input(item) for item in performances]
    result = compute_cgpa(graded)
    return GpaRead(
        status=result.status,
        value=result.value,
        credited_courses=result.credited_courses,
        total_credits=result.total_credits,
        semester=None,
        message=result.message,
    )


def get_summary(db: Session, student_id: int) -> AcademicSummary:
    courses = list_course_performance(db, student_id)
    completed = sum(1 for item in courses if item.status == "complete")
    incomplete = sum(1 for item in courses if item.status == "incomplete")
    return AcademicSummary(
        enrolled_courses=len(courses),
        completed_courses=completed,
        incomplete_courses=incomplete,
        gpa=get_semester_gpa(db, student_id),
        cgpa=get_cgpa(db, student_id),
        courses=courses,
    )


def _build_course_performance(
    db: Session,
    enrollment: Enrollment,
    marks: list[CourseMark],
) -> CoursePerformance:
    scheme = grading_scheme_service.resolve_scheme_for_course(db, enrollment.course.grading_scheme_id)
    weights = {weight.assessment_type: weight.weight_percent for weight in scheme.weights}
    assessment_inputs = [
        WeightedAssessmentInput(
            assessment_type=mark.assessment_type,
            marks_obtained=mark.marks_obtained,
            maximum_marks=mark.maximum_marks,
            weight_percent=weights.get(mark.assessment_type, 0.0),
        )
        for mark in marks
    ]
    score_result = compute_course_score(assessment_inputs, weights)

    grade_letter = None
    grade_point = None
    if score_result.status == "complete" and score_result.final_score is not None:
        bands = [
            GradeBandRule(
                letter=band.letter,
                min_score=band.min_score,
                max_score=band.max_score,
                grade_point=band.grade_point,
            )
            for band in scheme.grade_bands
        ]
        grade = compute_grade(score_result.final_score, bands)
        grade_letter = grade.letter
        grade_point = grade.grade_point

    return CoursePerformance(
        course=enrollment.course,
        semester=enrollment.semester,
        credits=enrollment.course.credits,
        status=score_result.status,
        final_score=score_result.final_score,
        grade=grade_letter,
        grade_point=grade_point,
        missing_assessment_types=score_result.missing_assessment_types,
        message=score_result.message,
        assessments=[
            AssessmentPerformance(
                assessment_type=item.assessment_type,
                marks_obtained=item.marks_obtained,
                maximum_marks=item.maximum_marks,
                weight_percent=item.weight_percent,
                normalized_score=item.normalized_score,
                weighted_contribution=item.weighted_contribution,
            )
            for item in score_result.assessments
        ],
    )


def _to_graded_input(performance: CoursePerformance) -> GradedCourseInput:
    return GradedCourseInput(
        course_id=performance.course.id,
        credits=performance.credits,
        grade_point=performance.grade_point or 0.0,
        status=performance.status,
    )


def _active_enrollments(db: Session, student_id: int) -> list[Enrollment]:
    statement = (
        select(Enrollment)
        .where(Enrollment.student_id == student_id, Enrollment.status == "enrolled")
        .options(joinedload(Enrollment.course))
        .order_by(Enrollment.id)
    )
    return list(db.scalars(statement).unique().all())


def _marks_by_course(db: Session, student_id: int) -> dict[int, list[CourseMark]]:
    statement = (
        select(CourseMark)
        .where(CourseMark.student_id == student_id)
        .order_by(CourseMark.course_id, CourseMark.assessment_type)
    )
    grouped: dict[int, list[CourseMark]] = defaultdict(list)
    for mark in db.scalars(statement).all():
        grouped[mark.course_id].append(mark)
    return grouped
