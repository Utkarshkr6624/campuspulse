from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.core.exam_types import ExamType
from app.db.session import get_db
from app.models.student import Student
from app.schemas.exam import ExamCreate, ExamRead, ExamUpdate
from app.services import exam_service

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=list[ExamRead])
def list_exams(
    upcoming: bool | None = Query(default=None),
    course_id: int | None = Query(default=None),
    exam_type: ExamType | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[ExamRead]:
    exams = exam_service.list_exams(
        db,
        student.id,
        upcoming=upcoming,
        course_id=course_id,
        exam_type=exam_type,
        date_from=date_from,
        date_to=date_to,
    )
    return [exam_service.serialize_exam(item) for item in exams]


@router.get("/{exam_id}", response_model=ExamRead)
def get_exam(
    exam_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ExamRead:
    return exam_service.serialize_exam(exam_service.get_exam(db, student.id, exam_id))


@router.post("", response_model=ExamRead, status_code=status.HTTP_201_CREATED)
def create_exam(
    data: ExamCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ExamRead:
    return exam_service.serialize_exam(exam_service.create_exam(db, student.id, data))


@router.patch("/{exam_id}", response_model=ExamRead)
def update_exam(
    exam_id: int,
    data: ExamUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ExamRead:
    return exam_service.serialize_exam(exam_service.update_exam(db, student.id, exam_id, data))


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    exam_service.delete_exam(db, student.id, exam_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
