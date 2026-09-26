from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.academic_config import (
    DEFAULT_ASSESSMENT_WEIGHTS,
    DEFAULT_GRADE_BANDS,
    DEFAULT_SCHEME_CODE,
    DEFAULT_SCHEME_NAME,
)
from app.core.exceptions import NotFoundError
from app.models.grading import AssessmentWeight, GradeBand, GradingScheme


def ensure_default_scheme(db: Session) -> GradingScheme:
    existing = db.scalar(
        select(GradingScheme)
        .where(GradingScheme.code == DEFAULT_SCHEME_CODE)
        .options(joinedload(GradingScheme.weights), joinedload(GradingScheme.grade_bands))
    )
    if existing is not None:
        return existing

    scheme = GradingScheme(code=DEFAULT_SCHEME_CODE, name=DEFAULT_SCHEME_NAME, is_default=True)
    db.add(scheme)
    db.flush()
    for assessment_type, weight in DEFAULT_ASSESSMENT_WEIGHTS.items():
        db.add(
            AssessmentWeight(
                scheme_id=scheme.id,
                assessment_type=assessment_type.value,
                weight_percent=weight,
            )
        )
    for letter, min_score, max_score, grade_point in DEFAULT_GRADE_BANDS:
        db.add(
            GradeBand(
                scheme_id=scheme.id,
                letter=letter,
                min_score=min_score,
                max_score=max_score,
                grade_point=grade_point,
            )
        )
    db.commit()
    return get_scheme(db, scheme.id)


def get_scheme(db: Session, scheme_id: int) -> GradingScheme:
    statement = (
        select(GradingScheme)
        .where(GradingScheme.id == scheme_id)
        .options(joinedload(GradingScheme.weights), joinedload(GradingScheme.grade_bands))
    )
    scheme = db.scalars(statement).unique().first()
    if scheme is None:
        raise NotFoundError("Grading scheme not found.")
    return scheme


def get_default_scheme(db: Session) -> GradingScheme:
    statement = (
        select(GradingScheme)
        .where(GradingScheme.is_default.is_(True))
        .options(joinedload(GradingScheme.weights), joinedload(GradingScheme.grade_bands))
    )
    scheme = db.scalars(statement).unique().first()
    if scheme is None:
        return ensure_default_scheme(db)
    return scheme


def resolve_scheme_for_course(db: Session, course_scheme_id: int | None) -> GradingScheme:
    if course_scheme_id is None:
        return get_default_scheme(db)
    return get_scheme(db, course_scheme_id)
