from pydantic import BaseModel, Field

from app.core.analytics_config import AttendanceHealth, InsightSeverity, InsightType
from app.schemas.academic import GpaRead
from app.schemas.course_mark import CourseSummary


class GradeDistributionBucket(BaseModel):
    letter: str
    count: int


class AttentionCourse(BaseModel):
    course: CourseSummary
    reasons: list[str]


class AnalyticsOverview(BaseModel):
    gpa: GpaRead
    cgpa: GpaRead
    total_courses: int
    completed_courses: int
    incomplete_courses: int
    total_credits: int
    completed_credits: int
    overall_attendance: float | None
    grade_distribution: list[GradeDistributionBucket]
    courses_requiring_attention: list[AttentionCourse]
    available_grade_letters: list[str]
    data_status: str
    message: str | None = None


class CourseAnalytics(BaseModel):
    course: CourseSummary
    semester: str
    credits: int
    status: str
    current_score: float | None
    grade: str | None
    grade_point: float | None
    completed_assessments: int
    required_assessments: int
    missing_assessments: list[str]
    attendance_percentage: float | None
    attendance_health: AttendanceHealth
    message: str | None = None


class PerformancePoint(BaseModel):
    assessment_name: str
    assessment_type: str
    assessment_date: str | None
    percentage: float
    course: CourseSummary
    change_from_previous: float | None = None


class PerformanceTrend(BaseModel):
    status: str
    points: list[PerformancePoint]
    message: str | None = None


class AttendanceCourseAnalytics(BaseModel):
    course: CourseSummary
    attended: int
    total: int
    missed: int
    percentage: float | None
    health: AttendanceHealth
    message: str


class AttendanceAnalytics(BaseModel):
    overall_percentage: float | None
    overall_health: AttendanceHealth
    overall_message: str
    courses: list[AttendanceCourseAnalytics]


class AcademicInsight(BaseModel):
    id: str
    type: InsightType
    severity: InsightSeverity
    title: str
    message: str
    course_id: int | None = None
    course_code: str | None = None
    supporting_value: float | str | None = None
    navigation_target: str | None = None


class InsightsResponse(BaseModel):
    insights: list[AcademicInsight]
    status: str
    message: str | None = None


class GpaSimulationCourseInput(BaseModel):
    course_id: int
    letter_grade: str = Field(min_length=1, max_length=8)


class GpaSimulationRequest(BaseModel):
    courses: list[GpaSimulationCourseInput] = Field(default_factory=list)


class GpaSimulationCourseResult(BaseModel):
    course: CourseSummary
    credits: int
    source: str
    letter_grade: str | None
    grade_point: float | None


class GpaSimulationResponse(BaseModel):
    label: str = "Projected / Hypothetical"
    current_gpa: GpaRead
    projected_gpa: GpaRead
    courses: list[GpaSimulationCourseResult]
    message: str | None = None
