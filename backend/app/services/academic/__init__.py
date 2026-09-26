"""Academic calculation layers for CampusPulse.

Pipeline:

raw marks
    -> assessment normalization
    -> weighted course score
    -> letter grade
    -> grade point
    -> semester GPA
    -> CGPA
"""

from app.services.academic.course_score import CourseScoreResult, WeightedAssessmentInput, compute_course_score
from app.services.academic.gpa import GradedCourseInput, GpaResult, compute_cgpa, compute_gpa
from app.services.academic.grades import GradeBandRule, GradeResult, compute_grade, letter_to_grade_point, score_to_letter
from app.services.academic.percentages import assessment_percentage, normalize_assessment

__all__ = [
    "CourseScoreResult",
    "GradeBandRule",
    "GradeResult",
    "GradedCourseInput",
    "GpaResult",
    "WeightedAssessmentInput",
    "assessment_percentage",
    "compute_cgpa",
    "compute_course_score",
    "compute_grade",
    "compute_gpa",
    "letter_to_grade_point",
    "normalize_assessment",
    "score_to_letter",
]
