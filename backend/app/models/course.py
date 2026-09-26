from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    credits: Mapped[int] = mapped_column(Integer)
    grading_scheme_id: Mapped[int | None] = mapped_column(
        ForeignKey("grading_schemes.id"),
        nullable=True,
        index=True,
    )

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")
    marks: Mapped[list["CourseMark"]] = relationship(back_populates="course")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="course")
    exams: Mapped[list["Exam"]] = relationship(back_populates="course")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="course")
    grading_scheme: Mapped["GradingScheme | None"] = relationship(back_populates="courses")
