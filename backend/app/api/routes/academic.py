from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.academic import AcademicSummary, CoursePerformance, GpaRead
from app.services import academic_service

router = APIRouter(prefix="/academic", tags=["academic"])


@router.get("/courses", response_model=list[CoursePerformance])
def academic_courses(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[CoursePerformance]:
    return academic_service.list_course_performance(db, student.id)


@router.get("/gpa", response_model=GpaRead)
def academic_gpa(
    semester: str | None = Query(default=None),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> GpaRead:
    return academic_service.get_semester_gpa(db, student.id, semester)


@router.get("/cgpa", response_model=GpaRead)
def academic_cgpa(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> GpaRead:
    return academic_service.get_cgpa(db, student.id)


@router.get("/summary", response_model=AcademicSummary)
def academic_summary(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AcademicSummary:
    return academic_service.get_summary(db, student.id)
