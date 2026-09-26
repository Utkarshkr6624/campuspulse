from sqlalchemy import CheckConstraint, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin


class AcademicTarget(TimestampMixin, Base):
    __tablename__ = "academic_targets"
    __table_args__ = (
        UniqueConstraint("student_id", "target_type", name="uq_academic_target_student_type"),
        CheckConstraint("target_type IN ('SGPA', 'CGPA')", name="ck_academic_target_type"),
        CheckConstraint("target_value >= 0 AND target_value <= 10", name="ck_academic_target_value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[str] = mapped_column(String(8))
    target_value: Mapped[float] = mapped_column()


class WhatIfScenario(TimestampMixin, Base):
    __tablename__ = "what_if_scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    assessments: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
