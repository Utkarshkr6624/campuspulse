"""Configurable academic grading defaults.

Courses can point at a grading scheme row. Seeded defaults live here so
weights and letter bands are not scattered through services or the UI.
"""

from app.core.assessment_types import AssessmentType

# Default assessment weights as percentages. Must sum to 100.
DEFAULT_ASSESSMENT_WEIGHTS: dict[AssessmentType, float] = {
    AssessmentType.CAT1: 15.0,
    AssessmentType.CAT2: 15.0,
    AssessmentType.INTERNAL: 20.0,
    AssessmentType.FAT: 40.0,
    AssessmentType.LAB: 10.0,
    AssessmentType.ASSIGNMENT: 0.0,
    AssessmentType.OTHER: 0.0,
}

# Inclusive lower bound, exclusive upper bound except the top band.
# Each tuple: (letter, min_score, max_score, grade_point)
DEFAULT_GRADE_BANDS: list[tuple[str, float, float, float]] = [
    ("S", 90.0, 100.0, 10.0),
    ("A", 80.0, 90.0, 9.0),
    ("B", 70.0, 80.0, 8.0),
    ("C", 60.0, 70.0, 7.0),
    ("D", 55.0, 60.0, 6.0),
    ("E", 50.0, 55.0, 5.0),
    ("F", 0.0, 50.0, 0.0),
]

DEFAULT_SCHEME_CODE = "DEFAULT"
DEFAULT_SCHEME_NAME = "Default university scheme"
