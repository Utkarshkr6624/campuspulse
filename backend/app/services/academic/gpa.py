"""Semester GPA and cumulative CGPA."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GradedCourseInput:
    course_id: int
    credits: int
    grade_point: float
    status: str


@dataclass(frozen=True)
class GpaResult:
    status: str
    value: float | None
    credited_courses: int
    total_credits: float
    message: str | None


def compute_gpa(courses: list[GradedCourseInput]) -> GpaResult:
    """Credit-weighted GPA for a set of graded courses."""
    eligible = [course for course in courses if course.status == "complete"]
    if not eligible:
        incomplete = [course for course in courses if course.status == "incomplete"]
        if incomplete:
            return GpaResult(
                status="incomplete",
                value=None,
                credited_courses=0,
                total_credits=0.0,
                message="Complete weighted assessments for enrolled courses before GPA can be calculated.",
            )
        return GpaResult(
            status="unavailable",
            value=None,
            credited_courses=0,
            total_credits=0.0,
            message="Add assessment marks to calculate GPA.",
        )

    credit_total = 0.0
    point_total = 0.0
    for course in eligible:
        if course.credits <= 0:
            return GpaResult(
                status="invalid",
                value=None,
                credited_courses=0,
                total_credits=0.0,
                message="A graded course has zero credits, so GPA cannot be calculated.",
            )
        credit_total += course.credits
        point_total += course.grade_point * course.credits

    if credit_total <= 0:
        return GpaResult(
            status="invalid",
            value=None,
            credited_courses=0,
            total_credits=0.0,
            message="Total credits must be greater than zero.",
        )

    return GpaResult(
        status="complete",
        value=round(point_total / credit_total, 2),
        credited_courses=len(eligible),
        total_credits=credit_total,
        message=None,
    )


def compute_cgpa(courses: list[GradedCourseInput]) -> GpaResult:
    """CGPA uses the same credit-weighted formula across all completed courses."""
    return compute_gpa(courses)
