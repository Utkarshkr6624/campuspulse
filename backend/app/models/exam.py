from datetime import date, time

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.exam_types import EXAM_TYPE_VALUES
from app.db.session import Base
from app.models.mixins import TimestampMixin

_exam_type_values = ", ".join(f"'{value}'" for value in EXAM_TYPE_VALUES)


class Exam(TimestampMixin, Base):
    __tablename__ = "exams"
    __table_args__ = (
        CheckConstraint(f"exam_type IN ({_exam_type_values})", name="ck_exam_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    exam_type: Mapped[str] = mapped_column(String(32))
    exam_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship(back_populates="exams")
    course: Mapped["Course"] = relationship(back_populates="exams")
