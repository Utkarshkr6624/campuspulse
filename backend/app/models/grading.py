from sqlalchemy import Boolean, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class GradingScheme(TimestampMixin, Base):
    __tablename__ = "grading_schemes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    weights: Mapped[list["AssessmentWeight"]] = relationship(back_populates="scheme")
    grade_bands: Mapped[list["GradeBand"]] = relationship(back_populates="scheme")
    courses: Mapped[list["Course"]] = relationship(back_populates="grading_scheme")


class AssessmentWeight(TimestampMixin, Base):
    __tablename__ = "assessment_weights"
    __table_args__ = (
        UniqueConstraint("scheme_id", "assessment_type", name="uq_assessment_weight_scheme_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("grading_schemes.id"), index=True)
    assessment_type: Mapped[str] = mapped_column(String(32))
    weight_percent: Mapped[float] = mapped_column(Float)

    scheme: Mapped["GradingScheme"] = relationship(back_populates="weights")


class GradeBand(TimestampMixin, Base):
    __tablename__ = "grade_bands"
    __table_args__ = (
        UniqueConstraint("scheme_id", "letter", name="uq_grade_band_scheme_letter"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("grading_schemes.id"), index=True)
    letter: Mapped[str] = mapped_column(String(8))
    min_score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float)
    grade_point: Mapped[float] = mapped_column(Float)

    scheme: Mapped["GradingScheme"] = relationship(back_populates="grade_bands")
