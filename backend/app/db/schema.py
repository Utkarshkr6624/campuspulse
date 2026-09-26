from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.session import Base, SessionLocal, engine
from app.models.course import Course
from app.models.course_mark import CourseMark
from app.services import grading_scheme_service

_IDENTITY_COLUMNS = {"full_name", "university_id", "password_hash"}


def prepare_database() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    _check_legacy_duplicate_records(tables)
    if "students" in tables:
        columns = {column["name"] for column in inspector.get_columns("students")}
        if not _IDENTITY_COLUMNS.issubset(columns):
            missing = ", ".join(sorted(_IDENTITY_COLUMNS - columns))
            raise RuntimeError(
                "The existing students table is missing required identity columns "
                f"({missing}). Startup stopped without changing the database; "
                "review and migrate this schema explicitly."
            )
    Base.metadata.create_all(bind=engine)
    _ensure_column("courses", "owner_id", "INTEGER REFERENCES students(id) ON DELETE CASCADE")
    _ensure_column("courses", "grading_scheme_id", "INTEGER")
    _ensure_column("students", "official_cgpa", "FLOAT")
    _ensure_column("semesters", "academic_year", "VARCHAR(16)")
    _ensure_column("semesters", "recorded_sgpa", "FLOAT")
    _ensure_column("semesters", "recorded_credits", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column("enrollments", "semester", "VARCHAR(64) NOT NULL DEFAULT 'Current'")
    _ensure_column("students", "role", "VARCHAR(16) NOT NULL DEFAULT 'STUDENT'")
    _ensure_column("students", "token_version", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column("enrollments", "semester_id", "INTEGER REFERENCES semesters(id)")
    _migrate_course_ownership_indexes()
    _migrate_custom_assessments()
    _migrate_duplicate_event_indexes()
    _backfill_semesters()
    db = SessionLocal()
    try:
        grading_scheme_service.ensure_default_scheme(db)
    finally:
        db.close()


def _migrate_course_ownership_indexes() -> None:
    inspector = inspect(engine)
    if "courses" not in inspector.get_table_names():
        return
    indexes = {item["name"]: item for item in inspector.get_indexes("courses")}
    legacy = indexes.get("ix_courses_code")
    if legacy and legacy.get("unique"):
        with engine.begin() as connection:
            connection.execute(text("DROP INDEX IF EXISTS ix_courses_code"))
    inspector = inspect(engine)
    existing = {item["name"] for item in inspector.get_indexes("courses")}
    for index in Course.__table__.indexes:
        if index.name not in existing:
            index.create(bind=engine, checkfirst=True)


def _migrate_custom_assessments() -> None:
    inspector = inspect(engine)
    if "course_marks" not in inspector.get_table_names():
        return
    if engine.dialect.name == "postgresql":
        constraints = {item["name"] for item in inspector.get_check_constraints("course_marks")}
        if "ck_course_mark_assessment_type" in constraints or any(
            column["name"] == "assessment_type" and getattr(column["type"], "length", None) != 64
            for column in inspector.get_columns("course_marks")
        ):
            with engine.begin() as connection:
                if "ck_course_mark_assessment_type" in constraints:
                    connection.execute(text(
                        "ALTER TABLE course_marks DROP CONSTRAINT ck_course_mark_assessment_type"
                    ))
                connection.execute(text(
                    "ALTER TABLE course_marks ALTER COLUMN assessment_type TYPE VARCHAR(64)"
                ))
        return
    if engine.dialect.name != "sqlite":
        return
    with engine.connect() as connection:
        create_sql = connection.execute(text(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='course_marks'"
        )).scalar_one_or_none()
    if not create_sql or "ck_course_mark_assessment_type" not in create_sql:
        return

    # Rebuild only this table to remove the old enum CHECK while copying every row unchanged.
    raw = engine.raw_connection()
    cursor = raw.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("ALTER TABLE course_marks RENAME TO course_marks_legacy")
        for item in cursor.execute("PRAGMA index_list(course_marks_legacy)").fetchall():
            index_name = item[1]
            if not index_name.startswith("sqlite_autoindex"):
                cursor.execute(f'DROP INDEX "{index_name}"')
        cursor.execute(str(CreateTable(CourseMark.__table__).compile(engine)))
        columns = [column.name for column in CourseMark.__table__.columns]
        quoted = ", ".join(f'"{column}"' for column in columns)
        cursor.execute(
            f"INSERT INTO course_marks ({quoted}) SELECT {quoted} FROM course_marks_legacy"
        )
        cursor.execute("DROP TABLE course_marks_legacy")
        for index in CourseMark.__table__.indexes:
            cursor.execute(str(CreateIndex(index).compile(engine)))
        raw.commit()
        cursor.execute("PRAGMA foreign_keys=ON")
    except Exception:
        raw.rollback()
        raise
    finally:
        cursor.close()
        raw.close()


def _migrate_duplicate_event_indexes() -> None:
    checks = {
        "exams": ("uq_exam_student_course_title_type_date", "student_id, course_id, title, exam_type, exam_date"),
        "assignments": ("uq_assignment_student_course_title_due_date", "student_id, course_id, title, due_date"),
    }
    tables = set(inspect(engine).get_table_names())
    with engine.begin() as connection:
        for table, (index_name, columns) in checks.items():
            if table not in tables:
                continue
            expected = tuple(part.strip() for part in columns.split(","))
            unique_constraints = {
                tuple(item["column_names"])
                for item in inspect(engine).get_unique_constraints(table)
            }
            if expected in unique_constraints:
                continue
            connection.execute(text(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})"
            ))


def _check_legacy_duplicate_records(tables: set[str]) -> None:
    """Stop safely if existing data would prevent installing duplicate guards."""
    checks = {
        "exams": "student_id, course_id, title, exam_type, exam_date",
        "assignments": "student_id, course_id, title, due_date",
    }
    with engine.connect() as connection:
        for table, columns in checks.items():
            if table not in tables:
                continue
            duplicates = connection.execute(
                text(
                    f"SELECT 1 FROM {table} GROUP BY {columns} "
                    "HAVING COUNT(*) > 1 LIMIT 1"
                )
            ).first()
            if duplicates is not None:
                raise RuntimeError(
                    f"Duplicate {table} records prevent installing integrity constraints. "
                    "Review those records before restarting; no data was changed."
                )


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
