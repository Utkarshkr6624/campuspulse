from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.core.assignment_enums import AssignmentPriority, AssignmentStatus
from app.db.session import get_db
from app.models.student import Student
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate
from app.services import assignment_service

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("", response_model=list[AssignmentRead])
def list_assignments(
    upcoming: bool | None = Query(default=None),
    completed: bool | None = Query(default=None),
    course_id: int | None = Query(default=None),
    priority: AssignmentPriority | None = Query(default=None),
    status: AssignmentStatus | None = Query(default=None),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[AssignmentRead]:
    assignments = assignment_service.list_assignments(
        db,
        student.id,
        upcoming=upcoming,
        completed=completed,
        course_id=course_id,
        priority=priority,
        status=status,
    )
    return [assignment_service.serialize_assignment(item) for item in assignments]


@router.get("/{assignment_id}", response_model=AssignmentRead)
def get_assignment(
    assignment_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AssignmentRead:
    return assignment_service.serialize_assignment(
        assignment_service.get_assignment(db, student.id, assignment_id)
    )


@router.post("", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(
    data: AssignmentCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AssignmentRead:
    return assignment_service.serialize_assignment(
        assignment_service.create_assignment(db, student.id, data)
    )


@router.patch("/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AssignmentRead:
    return assignment_service.serialize_assignment(
        assignment_service.update_assignment(db, student.id, assignment_id, data)
    )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    assignment_service.delete_assignment(db, student.id, assignment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
