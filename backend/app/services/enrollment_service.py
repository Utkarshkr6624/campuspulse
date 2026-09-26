from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import commit_or_conflict
from app.models.enrollment import Enrollment
from app.models.semester import Semester
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate
from app.services import course_service


def list_enrollments(db: Session, student_id: int, skip: int, limit: int) -> list[Enrollment]:
    statement = (
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .order_by(Enrollment.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def get_enrollment(db: Session, student_id: int, enrollment_id: int) -> Enrollment:
    enrollment = db.get(Enrollment, enrollment_id)
    if enrollment is None or enrollment.student_id != student_id:
        raise NotFoundError("Enrollment not found.")
    return enrollment


def create_enrollment(db: Session, student_id: int, data: EnrollmentCreate) -> Enrollment:
    course_service.get_course(db, data.course_id)
    enrollment = Enrollment(
        student_id=student_id,
        course_id=data.course_id,
        status=data.status,
        semester=data.semester,
        semester_id=db.scalar(
            select(Semester.id).where(Semester.student_id == student_id, Semester.is_current.is_(True))
        ),
    )
    db.add(enrollment)
    commit_or_conflict(db, "You are already enrolled in this course.")
    db.refresh(enrollment)
    return enrollment


def update_enrollment(
    db: Session,
    student_id: int,
    enrollment_id: int,
    data: EnrollmentUpdate,
) -> Enrollment:
    enrollment = get_enrollment(db, student_id, enrollment_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(enrollment, field, value)
    commit_or_conflict(db, "Enrollment could not be updated.")
    db.refresh(enrollment)
    return enrollment


def delete_enrollment(db: Session, student_id: int, enrollment_id: int) -> None:
    enrollment = get_enrollment(db, student_id, enrollment_id)
    db.delete(enrollment)
    commit_or_conflict(db, "Enrollment could not be deleted.")


def count_active_enrollments(db: Session, student_id: int) -> int:
    statement = select(Enrollment).where(
        Enrollment.student_id == student_id,
        Enrollment.status == "enrolled",
    )
    return len(list(db.scalars(statement).all()))
