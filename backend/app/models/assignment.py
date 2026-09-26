from datetime import date, time

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.assignment_enums import ASSIGNMENT_PRIORITY_VALUES, ASSIGNMENT_STATUS_VALUES
from app.db.session import Base
from app.models.mixins import TimestampMixin

_status_values = ", ".join(f"'{value}'" for value in ASSIGNMENT_STATUS_VALUES)
_priority_values = ", ".join(f"'{value}'" for value in ASSIGNMENT_PRIORITY_VALUES)


class Assignment(TimestampMixin, Base):
    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint(f"status IN ({_status_values})", name="ck_assignment_status"),
        CheckConstraint(f"priority IN ({_priority_values})", name="ck_assignment_priority"),
        UniqueConstraint(
            "student_id", "course_id", "title", "due_date",
            name="uq_assignment_student_course_title_due_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    due_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="TODO", index=True)
    priority: Mapped[str] = mapped_column(String(32), default="MEDIUM", index=True)

    student: Mapped["Student"] = relationship(back_populates="assignments")
    course: Mapped["Course"] = relationship(back_populates="assignments")
