from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.roles import DEFAULT_USER_ROLE
from app.db.session import Base
from app.models.mixins import TimestampMixin


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    university_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default=DEFAULT_USER_ROLE, index=True)

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")
    marks: Mapped[list["CourseMark"]] = relationship(back_populates="student")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="student")
    exams: Mapped[list["Exam"]] = relationship(back_populates="student")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="student")
    uploaded_documents: Mapped[list["Document"]] = relationship(back_populates="uploader")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="student")
    semesters: Mapped[list["Semester"]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="Semester.number"
    )
