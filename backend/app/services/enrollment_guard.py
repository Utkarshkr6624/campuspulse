from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models.enrollment import Enrollment


def require_active_enrollment(db: Session, student_id: int, course_id: int) -> Enrollment:
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
            Enrollment.status == "enrolled",
        )
    )
    if enrollment is None:
        raise ConflictError("Enroll in the course before adding this record.")
    return enrollment


def days_until(target: date, today: date | None = None) -> int:
    reference = today or date.today()
    return (target - reference).days
