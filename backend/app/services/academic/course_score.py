"""Course score aggregation from weighted assessments."""

from dataclasses import dataclass

from app.services.academic.percentages import normalize_assessment


@dataclass(frozen=True)
class WeightedAssessmentInput:
    assessment_type: str
    marks_obtained: float
    maximum_marks: float
    weight_percent: float


@dataclass(frozen=True)
class WeightedAssessmentResult:
    assessment_type: str
    marks_obtained: float
    maximum_marks: float
    weight_percent: float
    normalized_score: float
    weighted_contribution: float


@dataclass(frozen=True)
class CourseScoreResult:
    status: str
    final_score: float | None
    assessments: list[WeightedAssessmentResult]
    missing_assessment_types: list[str]
    message: str | None


def compute_course_score(
    assessments: list[WeightedAssessmentInput],
    required_weights: dict[str, float],
) -> CourseScoreResult:
    """Compute a weighted course score on a 0–100 scale.

    Only assessment types with weight_percent > 0 are required.
    Missing required assessments yield an incomplete result (not a zero score).
    """
    required_types = sorted(atype for atype, weight in required_weights.items() if weight > 0)
    by_type = {item.assessment_type: item for item in assessments}

    missing = [atype for atype in required_types if atype not in by_type]
    computed: list[WeightedAssessmentResult] = []

    for item in assessments:
        weight = required_weights.get(item.assessment_type, item.weight_percent)
        if weight <= 0:
            continue
        normalized = normalize_assessment(item.marks_obtained, item.maximum_marks)
        contribution = round(normalized * weight, 4)
        computed.append(
            WeightedAssessmentResult(
                assessment_type=item.assessment_type,
                marks_obtained=item.marks_obtained,
                maximum_marks=item.maximum_marks,
                weight_percent=weight,
                normalized_score=round(normalized * 100, 2),
                weighted_contribution=contribution,
            )
        )

    if not required_types:
        return CourseScoreResult(
            status="incomplete",
            final_score=None,
            assessments=computed,
            missing_assessment_types=[],
            message="No positive assessment weights are configured for this course.",
        )

    if not assessments:
        return CourseScoreResult(
            status="no_marks",
            final_score=None,
            assessments=[],
            missing_assessment_types=required_types,
            message="No assessment marks have been recorded for this course.",
        )

    if missing:
        return CourseScoreResult(
            status="incomplete",
            final_score=None,
            assessments=computed,
            missing_assessment_types=missing,
            message="Add the remaining weighted assessments before a course score can be calculated.",
        )

    final_score = round(sum(item.weighted_contribution for item in computed), 2)
    return CourseScoreResult(
        status="complete",
        final_score=final_score,
        assessments=computed,
        missing_assessment_types=[],
        message=None,
    )
