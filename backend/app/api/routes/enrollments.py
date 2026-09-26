from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.enrollment import EnrollmentCreate, EnrollmentRead, EnrollmentUpdate
from app.services import enrollment_service

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.get("", response_model=list[EnrollmentRead])
def list_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[EnrollmentRead]:
    return enrollment_service.list_enrollments(db, student.id, skip, limit)


@router.get("/{enrollment_id}", response_model=EnrollmentRead)
def get_enrollment(
    enrollment_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> EnrollmentRead:
    return enrollment_service.get_enrollment(db, student.id, enrollment_id)


@router.post("", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    data: EnrollmentCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> EnrollmentRead:
    return enrollment_service.create_enrollment(db, student.id, data)


@router.patch("/{enrollment_id}", response_model=EnrollmentRead)
def update_enrollment(
    enrollment_id: int,
    data: EnrollmentUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> EnrollmentRead:
    return enrollment_service.update_enrollment(db, student.id, enrollment_id, data)


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(
    enrollment_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    enrollment_service.delete_enrollment(db, student.id, enrollment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
