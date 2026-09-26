from pydantic import BaseModel

from app.schemas.course_mark import CourseSummary


class AssessmentPerformance(BaseModel):
    assessment_type: str
    marks_obtained: float
    maximum_marks: float
    weight_percent: float
    normalized_score: float
    weighted_contribution: float


class CoursePerformance(BaseModel):
    course: CourseSummary
    semester: str
    credits: int
    status: str
    final_score: float | None
    grade: str | None
    grade_point: float | None
    missing_assessment_types: list[str]
    message: str | None
    assessments: list[AssessmentPerformance]


class GpaRead(BaseModel):
    status: str
    value: float | None
    credited_courses: int
    total_credits: float
    semester: str | None = None
    message: str | None


class AcademicSummary(BaseModel):
    enrolled_courses: int
    completed_courses: int
    incomplete_courses: int
    gpa: GpaRead
    cgpa: GpaRead
    courses: list[CoursePerformance]
