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


class IntelligenceInsight(BaseModel):
    type: str
    severity: InsightSeverity
    title: str
    description: str
    supporting_data: dict[str, float | int | str | None]
    source_metric: str


class IntelligenceAssessment(BaseModel):
    assessment_type: str
    percentage: float


class IntelligenceCourse(BaseModel):
    semester_id: int | None
    semester_number: int | None
    course_id: int | None
    course_code: str | None
    course_name: str
    credits: int
    status: str
    score: float | None
    grade: str | None
    grade_point: float | None
    attendance_percentage: float | None
    attendance_health: AttendanceHealth
    performance_category: str
    assessments: list[IntelligenceAssessment]
    cat1_to_cat2_change: float | None


class SemesterTrendPoint(BaseModel):
    semester_id: int
    semester_number: int
    status: str
    sgpa: float | None
    cumulative_gpa: float | None
    completed_credits: int
    known_credits: int
    course_count: int
    average_marks: float | None
    gpa_change: float | None


class SemesterComparison(BaseModel):
    first_semester_id: int
    first_semester_number: int
    second_semester_id: int
    second_semester_number: int
    sgpa_difference: float | None
    average_marks_difference: float | None
    credits_difference: int
    course_count_difference: int
    attendance_difference: float | None = None
    attendance_note: str


class SemesterCreditPoint(BaseModel):
    semester_id: int
    semester_number: int
    known_credits: int
    completed_credits: int


class AcademicIntelligence(BaseModel):
    data_status: str
    message: str | None = None
    current_sgpa: float | None
    previous_sgpa: float | None
    sgpa_change: float | None
    cgpa: GpaRead
    completed_credits: int
    current_semester_credits: int
    total_known_credits: int
    average_marks: float | None
    overall_attendance: float | None
    completed_courses: int
    ongoing_courses: int
    attendance_warning_threshold: float
    attendance_healthy_threshold: float
    low_score_threshold: float
    strong_score_threshold: float
    semester_trend: list[SemesterTrendPoint]
    credits_by_semester: list[SemesterCreditPoint]
    courses: list[IntelligenceCourse]
    course_trends: list[dict[str, float | int | str | None]]
    insights: list[IntelligenceInsight]
    comparison: SemesterComparison | None = None
