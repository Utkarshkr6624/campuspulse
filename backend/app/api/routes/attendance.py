from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceOverview,
    AttendanceRead,
    AttendanceUpdate,
    CourseAttendanceSummary,
)
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("", response_model=list[AttendanceRead])
def list_attendance(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[AttendanceRead]:
    return [attendance_service.serialize_record(item) for item in attendance_service.list_records(db, student.id)]


@router.get("/overview", response_model=AttendanceOverview)
def attendance_overview(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AttendanceOverview:
    return attendance_service.build_overview(db, student.id)


@router.get("/courses/{course_id}", response_model=CourseAttendanceSummary)
def attendance_for_course(
    course_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> CourseAttendanceSummary:
    return attendance_service.course_summary(db, student.id, course_id)


@router.get("/{record_id}", response_model=AttendanceRead)
def get_attendance(
    record_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AttendanceRead:
    return attendance_service.serialize_record(attendance_service.get_record(db, student.id, record_id))


@router.post("", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def create_attendance(
    data: AttendanceCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AttendanceRead:
    return attendance_service.serialize_record(attendance_service.create_record(db, student.id, data))


@router.patch("/{record_id}", response_model=AttendanceRead)
def update_attendance(
    record_id: int,
    data: AttendanceUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AttendanceRead:
    return attendance_service.serialize_record(
        attendance_service.update_record(db, student.id, record_id, data)
    )


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    record_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    attendance_service.delete_record(db, student.id, record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
