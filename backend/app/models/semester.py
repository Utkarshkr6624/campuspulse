from sqlalchemy import CheckConstraint, ForeignKey, Float, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class Semester(TimestampMixin, Base):
    __tablename__ = "semesters"
    __table_args__ = (
        UniqueConstraint("student_id", "number", name="uq_semester_student_number"),
        CheckConstraint("number >= 1", name="ck_semester_number_positive"),
        Index(
            "uq_semester_student_current",
            "student_id",
            unique=True,
            sqlite_where=text("is_current = 1"),
            postgresql_where=text("is_current = true"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(default=False, index=True)

    student: Mapped["Student"] = relationship(back_populates="semesters")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="semester_record")
    history_courses: Mapped[list["SemesterCourse"]] = relationship(
        back_populates="semester", cascade="all, delete-orphan", order_by="SemesterCourse.id"
    )


class SemesterCourse(TimestampMixin, Base):
    """Student-owned historical course snapshot, optionally linked to the shared catalog."""

    __tablename__ = "semester_courses"
    __table_args__ = (
        UniqueConstraint("semester_id", "course_code", name="uq_semester_course_code"),
        CheckConstraint("credits > 0", name="ck_semester_course_credits_positive"),
        CheckConstraint("grade_point >= 0", name="ck_semester_course_grade_point"),
        CheckConstraint("final_score IS NULL OR (final_score >= 0 AND final_score <= 100)", name="ck_semester_course_score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    course_name: Mapped[str] = mapped_column(String(200))
    course_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    credits: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(8))
    grade_point: Mapped[float] = mapped_column(Float)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    course_component: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    semester: Mapped["Semester"] = relationship(back_populates="history_courses")
    course: Mapped["Course | None"] = relationship()
