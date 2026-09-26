from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"], dependencies=[Depends(get_current_student)])


@router.get("", response_model=list[StudentRead])
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[StudentRead]:
    return student_service.list_students(db, skip, limit)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)) -> StudentRead:
    return student_service.get_student(db, student_id)


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(data: StudentCreate, db: Session = Depends(get_db)) -> StudentRead:
    return student_service.create_student(db, data)


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
) -> StudentRead:
    return student_service.update_student(db, student_id, data)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)) -> Response:
    student_service.delete_student(db, student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
