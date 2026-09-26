from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.semester import (
    SemesterCourseCreate,
    SemesterCourseRead,
    SemesterCreate,
    SemesterDetail,
    SemesterHistoryCreate,
    SemesterRead,
    SemesterSetup,
    SemesterUpdate,
)
from app.services import semester_service

router = APIRouter(prefix="/semesters", tags=["semesters"])


@router.get("", response_model=list[SemesterRead])
def list_semesters(
    student: Student = Depends(get_current_student), db: Session = Depends(get_db)
) -> list[SemesterRead]:
    return semester_service.list_semesters(db, student.id)


@router.post("/setup", response_model=list[SemesterRead])
def setup_semesters(
    data: SemesterSetup,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[SemesterRead]:
    return semester_service.setup_semesters(db, student.id, data)


@router.post("", response_model=SemesterRead, status_code=status.HTTP_201_CREATED)
def create_semester(
    data: SemesterCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> SemesterRead:
    return semester_service.create_semester(db, student.id, data)


@router.get("/{semester_id}", response_model=SemesterDetail)
def get_semester(
    semester_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> SemesterDetail:
    return semester_service.get_semester_detail(db, student.id, semester_id)


@router.patch("/{semester_id}", response_model=SemesterRead)
def update_semester(
    semester_id: int,
    data: SemesterUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> SemesterRead:
    return semester_service.update_semester(db, student.id, semester_id, data)


@router.post("/{semester_id}/current", response_model=list[SemesterRead])
def set_current_semester(
    semester_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[SemesterRead]:
    return semester_service.set_current_semester(db, student.id, semester_id)


@router.delete("/{semester_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_semester(
    semester_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    semester_service.delete_semester(db, student.id, semester_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{semester_id}/courses", response_model=list[SemesterCourseRead], status_code=status.HTTP_201_CREATED)
def add_history_courses(
    semester_id: int,
    data: SemesterHistoryCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[SemesterCourseRead]:
    return semester_service.add_history_courses(db, student.id, semester_id, data.courses)


@router.patch("/{semester_id}/courses/{course_record_id}", response_model=SemesterCourseRead)
def update_history_course(
    semester_id: int,
    course_record_id: int,
    data: SemesterCourseCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> SemesterCourseRead:
    return semester_service.update_history_course(
        db, student.id, semester_id, course_record_id, data
    )


@router.delete("/{semester_id}/courses/{course_record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_course(
    semester_id: int,
    course_record_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    semester_service.delete_history_course(db, student.id, semester_id, course_record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
