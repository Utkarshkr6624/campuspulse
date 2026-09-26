from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.exam_types import ExamType
from app.db.session import commit_or_conflict
from app.models.exam import Exam
from app.schemas.exam import ExamCreate, ExamRead, ExamUpdate
from app.services import course_service
from app.services.enrollment_guard import days_until, require_active_enrollment


def list_exams(
    db: Session,
    student_id: int,
    *,
    upcoming: bool | None = None,
    course_id: int | None = None,
    exam_type: ExamType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Exam]:
    statement = _base_query(student_id)
    statement = _apply_filters(
        statement,
        upcoming=upcoming,
        course_id=course_id,
        exam_type=exam_type.value if exam_type else None,
        date_from=date_from,
        date_to=date_to,
    )
    statement = statement.order_by(Exam.exam_date.asc(), Exam.start_time.asc(), Exam.id.asc())
    return list(db.scalars(statement).unique().all())


def get_exam(db: Session, student_id: int, exam_id: int) -> Exam:
    statement = _base_query(student_id).where(Exam.id == exam_id)
    exam = db.scalars(statement).unique().first()
    if exam is None:
        raise NotFoundError("Exam not found.")
    return exam


def create_exam(db: Session, student_id: int, data: ExamCreate) -> Exam:
    course_service.get_course(db, data.course_id)
    require_active_enrollment(db, student_id, data.course_id)
    exam = Exam(
        student_id=student_id,
        course_id=data.course_id,
        title=data.title,
        exam_type=data.exam_type.value,
        exam_date=data.exam_date,
        start_time=data.start_time,
        end_time=data.end_time,
        location=data.location,
        description=data.description,
    )
    db.add(exam)
    commit_or_conflict(db, "Exam could not be created.")
    return get_exam(db, student_id, exam.id)


def update_exam(db: Session, student_id: int, exam_id: int, data: ExamUpdate) -> Exam:
    exam = get_exam(db, student_id, exam_id)
    changes = data.model_dump(exclude_unset=True)
    if "exam_type" in changes and changes["exam_type"] is not None:
        changes["exam_type"] = changes["exam_type"].value

    next_start = changes.get("start_time", exam.start_time)
    next_end = changes.get("end_time", exam.end_time)
    if next_start and next_end and next_end <= next_start:
        raise BadRequestError("end_time must be after start_time.")

    for field, value in changes.items():
        setattr(exam, field, value)
    commit_or_conflict(db, "Exam could not be updated.")
    return get_exam(db, student_id, exam.id)


def delete_exam(db: Session, student_id: int, exam_id: int) -> None:
    exam = get_exam(db, student_id, exam_id)
    db.delete(exam)
    commit_or_conflict(db, "Exam could not be deleted.")


def serialize_exam(exam: Exam, today: date | None = None) -> ExamRead:
    reference = today or date.today()
    until = days_until(exam.exam_date, reference)
    return ExamRead(
        id=exam.id,
        student_id=exam.student_id,
        course_id=exam.course_id,
        title=exam.title,
        exam_type=exam.exam_type,
        exam_date=exam.exam_date,
        start_time=exam.start_time,
        end_time=exam.end_time,
        location=exam.location,
        description=exam.description,
        created_at=exam.created_at,
        updated_at=exam.updated_at,
        course=exam.course,
        is_upcoming=until >= 0,
        days_until=until,
    )


def _base_query(student_id: int) -> Select[tuple[Exam]]:
    return (
        select(Exam)
        .where(Exam.student_id == student_id)
        .options(joinedload(Exam.course))
    )


def _apply_filters(
    statement: Select[tuple[Exam]],
    *,
    upcoming: bool | None,
    course_id: int | None,
    exam_type: str | None,
    date_from: date | None,
    date_to: date | None,
) -> Select[tuple[Exam]]:
    today = date.today()
    if upcoming is True:
        statement = statement.where(Exam.exam_date >= today)
    elif upcoming is False:
        statement = statement.where(Exam.exam_date < today)
    if course_id is not None:
        statement = statement.where(Exam.course_id == course_id)
    if exam_type is not None:
        statement = statement.where(Exam.exam_type == exam_type)
    if date_from is not None:
        statement = statement.where(Exam.exam_date >= date_from)
    if date_to is not None:
        statement = statement.where(Exam.exam_date <= date_to)
    return statement
