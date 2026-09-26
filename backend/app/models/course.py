from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class Course(TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        Index(
            "uq_courses_catalog_code",
            "code",
            unique=True,
            sqlite_where=text("owner_id IS NULL"),
            postgresql_where=text("owner_id IS NULL"),
        ),
        Index("uq_courses_owner_code", "owner_id", "code", unique=True),
        Index("ix_courses_code", "code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(200))
    credits: Mapped[int] = mapped_column(Integer)
    grading_scheme_id: Mapped[int | None] = mapped_column(
        ForeignKey("grading_schemes.id"),
        nullable=True,
        index=True,
    )
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")
    marks: Mapped[list["CourseMark"]] = relationship(back_populates="course")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="course")
    exams: Mapped[list["Exam"]] = relationship(back_populates="course")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="course")
    grading_scheme: Mapped["GradingScheme | None"] = relationship(back_populates="courses")
    owner: Mapped["Student | None"] = relationship()
