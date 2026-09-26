from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.roles import DEFAULT_USER_ROLE
from app.core.security import hash_password
from app.db.session import commit_or_conflict
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


def list_students(db: Session, skip: int, limit: int) -> list[Student]:
    statement = select(Student).order_by(Student.id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise NotFoundError("Student not found.")
    return student


def get_student_by_email(db: Session, email: str) -> Student | None:
    return db.scalar(select(Student).where(Student.email == email))


def create_student(db: Session, data: StudentCreate) -> Student:
    ensure_identity_available(db, email=data.email, university_id=data.university_id)
    student = Student(
        full_name=data.full_name,
        email=str(data.email),
        university_id=data.university_id,
        password_hash=hash_password(data.password),
        role=DEFAULT_USER_ROLE,
    )
    db.add(student)
    commit_or_conflict(db, "An account with that email or university ID already exists.")
    db.refresh(student)
    return student


def update_student(db: Session, student_id: int, data: StudentUpdate) -> Student:
    student = get_student(db, student_id)
    changes = data.model_dump(exclude_unset=True)
    ensure_identity_available(
        db,
        email=changes.get("email", student.email),
        university_id=changes.get("university_id", student.university_id),
        student_id=student.id,
    )
    for field, value in changes.items():
        setattr(student, field, value)
    commit_or_conflict(db, "An account with that email or university ID already exists.")
    db.refresh(student)
    return student


def delete_student(db: Session, student_id: int) -> None:
    student = get_student(db, student_id)
    db.delete(student)
    commit_or_conflict(db, "Student cannot be deleted while enrollments exist.")


def ensure_identity_available(
    db: Session,
    email: str,
    university_id: str,
    student_id: int | None = None,
) -> None:
    email_owner = db.scalar(select(Student).where(Student.email == email))
    if email_owner is not None and email_owner.id != student_id:
        raise ConflictError("An account with these details already exists.")
    id_owner = db.scalar(select(Student).where(Student.university_id == university_id))
    if id_owner is not None and id_owner.id != student_id:
        raise ConflictError("An account with these details already exists.")
