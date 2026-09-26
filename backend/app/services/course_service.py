from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import commit_or_conflict
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate


def list_courses(db: Session, skip: int, limit: int) -> list[Course]:
    statement = select(Course).order_by(Course.id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise NotFoundError("Course not found.")
    return course


def create_course(db: Session, data: CourseCreate) -> Course:
    course = Course(**data.model_dump())
    db.add(course)
    commit_or_conflict(db, "A course with that code already exists.")
    db.refresh(course)
    return course


def update_course(db: Session, course_id: int, data: CourseUpdate) -> Course:
    course = get_course(db, course_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    commit_or_conflict(db, "A course with that code already exists.")
    db.refresh(course)
    return course


def delete_course(db: Session, course_id: int) -> None:
    course = get_course(db, course_id)
    db.delete(course)
    commit_or_conflict(db, "Course cannot be deleted while enrollments exist.")
