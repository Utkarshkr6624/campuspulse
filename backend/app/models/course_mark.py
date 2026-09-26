from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.assessment_types import ASSESSMENT_TYPE_VALUES
from app.db.session import Base
from app.models.mixins import TimestampMixin

_assessment_values = ", ".join(f"'{value}'" for value in ASSESSMENT_TYPE_VALUES)


class CourseMark(TimestampMixin, Base):
    """Raw assessment score for a student in a course.

    Later academic layers (course score, grade, GPA) should read from this
    table rather than inventing parallel mark stores.
    """

    __tablename__ = "course_marks"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            "assessment_type",
            name="uq_course_mark_student_course_assessment",
        ),
        CheckConstraint(
            f"assessment_type IN ({_assessment_values})",
            name="ck_course_mark_assessment_type",
        ),
        CheckConstraint("maximum_marks > 0", name="ck_course_mark_maximum_positive"),
        CheckConstraint("marks_obtained >= 0", name="ck_course_mark_obtained_non_negative"),
        CheckConstraint(
            "marks_obtained <= maximum_marks",
            name="ck_course_mark_obtained_within_maximum",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    assessment_type: Mapped[str] = mapped_column(String(32))
    marks_obtained: Mapped[float] = mapped_column(Float)
    maximum_marks: Mapped[float] = mapped_column(Float)
    assessment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    student: Mapped["Student"] = relationship(back_populates="marks")
    course: Mapped["Course"] = relationship(back_populates="marks")
