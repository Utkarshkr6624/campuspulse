from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.core.assignment_enums import AssignmentPriority, AssignmentStatus
from app.core.exceptions import NotFoundError
from app.db.session import commit_or_conflict
from app.models.assignment import Assignment
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate
from app.services import course_service
from app.services.enrollment_guard import days_until, require_active_enrollment


def list_assignments(
    db: Session,
    student_id: int,
    *,
    upcoming: bool | None = None,
    completed: bool | None = None,
    course_id: int | None = None,
    priority: AssignmentPriority | None = None,
    status: AssignmentStatus | None = None,
) -> list[Assignment]:
    statement = _base_query(student_id)
    statement = _apply_filters(
        statement,
        upcoming=upcoming,
        completed=completed,
        course_id=course_id,
        priority=priority.value if priority else None,
        status=status.value if status else None,
    )
    statement = statement.order_by(Assignment.due_date.asc(), Assignment.due_time.asc(), Assignment.id.asc())
    return list(db.scalars(statement).unique().all())


def get_assignment(db: Session, student_id: int, assignment_id: int) -> Assignment:
    statement = _base_query(student_id).where(Assignment.id == assignment_id)
    assignment = db.scalars(statement).unique().first()
    if assignment is None:
        raise NotFoundError("Assignment not found.")
    return assignment


def create_assignment(db: Session, student_id: int, data: AssignmentCreate) -> Assignment:
    course_service.get_course(db, data.course_id, student_id)
    require_active_enrollment(db, student_id, data.course_id)
    assignment = Assignment(
        student_id=student_id,
        course_id=data.course_id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        due_time=data.due_time,
        status=data.status.value,
        priority=data.priority.value,
    )
    db.add(assignment)
    commit_or_conflict(db, "Assignment could not be created.")
    return get_assignment(db, student_id, assignment.id)


def update_assignment(
    db: Session,
    student_id: int,
    assignment_id: int,
    data: AssignmentUpdate,
) -> Assignment:
    assignment = get_assignment(db, student_id, assignment_id)
    changes = data.model_dump(exclude_unset=True)
    if "status" in changes and changes["status"] is not None:
        changes["status"] = changes["status"].value
    if "priority" in changes and changes["priority"] is not None:
        changes["priority"] = changes["priority"].value
    for field, value in changes.items():
        setattr(assignment, field, value)
    commit_or_conflict(db, "Assignment could not be updated.")
    return get_assignment(db, student_id, assignment.id)


def delete_assignment(db: Session, student_id: int, assignment_id: int) -> None:
    assignment = get_assignment(db, student_id, assignment_id)
    db.delete(assignment)
    commit_or_conflict(db, "Assignment could not be deleted.")


def serialize_assignment(assignment: Assignment, today: date | None = None) -> AssignmentRead:
    reference = today or date.today()
    until = days_until(assignment.due_date, reference)
    is_completed = assignment.status == AssignmentStatus.COMPLETED.value
    return AssignmentRead(
        id=assignment.id,
        student_id=assignment.student_id,
        course_id=assignment.course_id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        due_time=assignment.due_time,
        status=assignment.status,
        priority=assignment.priority,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        course=assignment.course,
        is_overdue=not is_completed and until < 0,
        is_due_today=not is_completed and until == 0,
        days_until=until,
    )


def _base_query(student_id: int) -> Select[tuple[Assignment]]:
    return (
        select(Assignment)
        .where(Assignment.student_id == student_id)
        .options(joinedload(Assignment.course))
    )


def _apply_filters(
    statement: Select[tuple[Assignment]],
    *,
    upcoming: bool | None,
    completed: bool | None,
    course_id: int | None,
    priority: str | None,
    status: str | None,
) -> Select[tuple[Assignment]]:
    today = date.today()
    if completed is True:
        statement = statement.where(Assignment.status == AssignmentStatus.COMPLETED.value)
    elif completed is False:
        statement = statement.where(Assignment.status != AssignmentStatus.COMPLETED.value)
    if upcoming is True:
        statement = statement.where(
            Assignment.status != AssignmentStatus.COMPLETED.value,
            Assignment.due_date >= today,
        )
    elif upcoming is False:
        statement = statement.where(Assignment.due_date < today)
    if course_id is not None:
        statement = statement.where(Assignment.course_id == course_id)
    if priority is not None:
        statement = statement.where(Assignment.priority == priority)
    if status is not None:
        statement = statement.where(Assignment.status == status)
    return statement
