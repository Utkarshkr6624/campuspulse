from app.core.academic_config import DEFAULT_ASSESSMENT_WEIGHTS, DEFAULT_GRADE_BANDS
from app.core.assessment_types import AssessmentType
from app.services.academic import (
    GradeBandRule,
    GradedCourseInput,
    WeightedAssessmentInput,
    compute_cgpa,
    compute_course_score,
    compute_gpa,
    compute_grade,
    letter_to_grade_point,
    normalize_assessment,
    score_to_letter,
)


def _bands() -> list[GradeBandRule]:
    return [
        GradeBandRule(letter=letter, min_score=low, max_score=high, grade_point=points)
        for letter, low, high, points in DEFAULT_GRADE_BANDS
    ]


def test_normalize_assessment():
    assert normalize_assessment(36, 50) == 0.72


def test_weighted_course_score_complete():
    weights = {atype.value: weight for atype, weight in DEFAULT_ASSESSMENT_WEIGHTS.items()}
    assessments = [
        WeightedAssessmentInput("CAT1", 36, 50, 15),
        WeightedAssessmentInput("CAT2", 42, 50, 15),
        WeightedAssessmentInput("INTERNAL", 27, 30, 20),
        WeightedAssessmentInput("FAT", 84, 100, 40),
        WeightedAssessmentInput("LAB", 18, 20, 10),
    ]
    result = compute_course_score(assessments, weights)
    assert result.status == "complete"
    assert result.final_score == 84.0
    assert result.missing_assessment_types == []


def test_weighted_course_score_missing_required():
    weights = {atype.value: weight for atype, weight in DEFAULT_ASSESSMENT_WEIGHTS.items()}
    assessments = [WeightedAssessmentInput("CAT1", 36, 50, 15)]
    result = compute_course_score(assessments, weights)
    assert result.status == "incomplete"
    assert result.final_score is None
    assert "FAT" in result.missing_assessment_types


def test_weighted_course_score_no_marks():
    weights = {atype.value: weight for atype, weight in DEFAULT_ASSESSMENT_WEIGHTS.items()}
    result = compute_course_score([], weights)
    assert result.status == "no_marks"
    assert result.final_score is None


def test_grade_conversion():
    bands = _bands()
    assert score_to_letter(84.0, bands) == "A"
    assert letter_to_grade_point("A", bands) == 9.0
    grade = compute_grade(84.0, bands)
    assert grade.letter == "A"
    assert grade.grade_point == 9.0
    assert score_to_letter(49.9, bands) == "F"
    assert score_to_letter(90, bands) == "S"


def test_semester_gpa_and_cgpa():
    courses = [
        GradedCourseInput(course_id=1, credits=4, grade_point=9.0, status="complete"),
        GradedCourseInput(course_id=2, credits=3, grade_point=8.0, status="complete"),
        GradedCourseInput(course_id=3, credits=3, grade_point=0.0, status="incomplete"),
    ]
    gpa = compute_gpa(courses)
    assert gpa.status == "complete"
    assert gpa.value == round(((9 * 4) + (8 * 3)) / 7, 2)
    assert gpa.credited_courses == 2

    cgpa = compute_cgpa(courses)
    assert cgpa.value == gpa.value


def test_gpa_unavailable_without_complete_courses():
    result = compute_gpa(
        [GradedCourseInput(course_id=1, credits=4, grade_point=0.0, status="incomplete")]
    )
    assert result.status == "incomplete"
    assert result.value is None


def test_gpa_rejects_zero_credits():
    result = compute_gpa(
        [GradedCourseInput(course_id=1, credits=0, grade_point=9.0, status="complete")]
    )
    assert result.status == "invalid"
    assert result.value is None
