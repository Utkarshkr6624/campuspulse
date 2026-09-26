from sqlalchemy import inspect, text

from app.db.session import Base, SessionLocal, engine
from app.services import grading_scheme_service

_IDENTITY_COLUMNS = {"full_name", "university_id", "password_hash"}


def prepare_database() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "students" in tables:
        columns = {column["name"] for column in inspector.get_columns("students")}
        if not _IDENTITY_COLUMNS.issubset(columns):
            _replace_empty_student_table(tables)
    Base.metadata.create_all(bind=engine)
    _ensure_column("courses", "grading_scheme_id", "INTEGER")
    _ensure_column("enrollments", "semester", "VARCHAR(64) NOT NULL DEFAULT 'Current'")
    _ensure_column("students", "role", "VARCHAR(16) NOT NULL DEFAULT 'STUDENT'")
    _ensure_column("enrollments", "semester_id", "INTEGER REFERENCES semesters(id)")
    _backfill_semesters()
    db = SessionLocal()
    try:
        grading_scheme_service.ensure_default_scheme(db)
    finally:
        db.close()


def _ensure_column(table: str, column: str, ddl_type: str) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    columns = {item["name"] for item in inspector.get_columns(table)}
    if column in columns:
        return
    with engine.connect() as connection:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
        connection.commit()


def _backfill_semesters() -> None:
    """Preserve recognizable semester labels without guessing the student's current term."""
    import re

    from sqlalchemy import select

    from app.models.enrollment import Enrollment
    from app.models.semester import Semester
    db = SessionLocal()
    try:
        changed = False
        enrollments = list(db.scalars(select(Enrollment).where(Enrollment.semester_id.is_(None))).all())
        for enrollment in enrollments:
            match = re.fullmatch(r"\s*semester\s+(\d+)\s*", enrollment.semester, re.IGNORECASE)
            if match is None:
                continue
            number = int(match.group(1))
            semester = db.scalar(
                select(Semester).where(
                    Semester.student_id == enrollment.student_id,
                    Semester.number == number,
                )
            )
            if semester is None:
                semester = Semester(student_id=enrollment.student_id, number=number, is_current=False)
                db.add(semester)
                db.flush()
            enrollment.semester_id = semester.id
            changed = True
        if changed:
            db.commit()
    finally:
        db.close()


def _replace_empty_student_table(tables: set[str]) -> None:
    with engine.connect() as connection:
        student_count = connection.execute(text("SELECT COUNT(*) FROM students")).scalar_one()
        enrollment_count = 0
        if "enrollments" in tables:
            enrollment_count = connection.execute(text("SELECT COUNT(*) FROM enrollments")).scalar_one()
        if student_count or enrollment_count:
            raise RuntimeError(
                "The students table is missing identity columns and already has rows. "
                "Startup was stopped so existing records are not deleted."
            )
        connection.execute(text("PRAGMA foreign_keys=OFF"))
        connection.execute(text("DROP TABLE students"))
        connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.commit()
