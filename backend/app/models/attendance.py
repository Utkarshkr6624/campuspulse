from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.attendance_status import ATTENDANCE_STATUS_VALUES
from app.db.session import Base
from app.models.mixins import TimestampMixin

_status_values = ", ".join(f"'{value}'" for value in ATTENDANCE_STATUS_VALUES)


class AttendanceRecord(TimestampMixin, Base):
    """One class session for a student in a course.

    Totals and percentages are derived in services, not stored.
    """

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            "attendance_date",
            name="uq_attendance_student_course_date",
        ),
        CheckConstraint(
            f"status IN ({_status_values})",
            name="ck_attendance_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    attendance_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="present")

    student: Mapped["Student"] = relationship(back_populates="attendance_records")
    course: Mapped["Course"] = relationship(back_populates="attendance_records")
