from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.analytics import (
    AnalyticsOverview,
    AttendanceAnalytics,
    CourseAnalytics,
    GpaSimulationRequest,
    GpaSimulationResponse,
    AcademicIntelligence,
    InsightsResponse,
    PerformanceTrend,
)
from app.services import analytics_service
from app.services import intelligence_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/intelligence", response_model=AcademicIntelligence)
def academic_intelligence(
    first_semester_id: int | None = None,
    second_semester_id: int | None = None,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AcademicIntelligence:
    return intelligence_service.get_academic_intelligence(
        db,
        student.id,
        first_semester_id=first_semester_id,
        second_semester_id=second_semester_id,
    )


@router.get("/overview", response_model=AnalyticsOverview)
def analytics_overview(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AnalyticsOverview:
    return analytics_service.get_overview(db, student.id)


@router.get("/courses", response_model=list[CourseAnalytics])
def analytics_courses(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[CourseAnalytics]:
    return analytics_service.list_course_analytics(db, student.id)


@router.get("/performance", response_model=PerformanceTrend)
def analytics_performance(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> PerformanceTrend:
    return analytics_service.get_performance_trend(db, student.id)


@router.get("/attendance", response_model=AttendanceAnalytics)
def analytics_attendance(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AttendanceAnalytics:
    return analytics_service.get_attendance_analytics(db, student.id)


@router.get("/insights", response_model=InsightsResponse)
def analytics_insights(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> InsightsResponse:
    return analytics_service.list_insights(db, student.id)


@router.post("/gpa-simulation", response_model=GpaSimulationResponse)
def analytics_gpa_simulation(
    payload: GpaSimulationRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> GpaSimulationResponse:
    return analytics_service.simulate_gpa(db, student.id, payload)
