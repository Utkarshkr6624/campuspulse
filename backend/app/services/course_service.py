from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.roles import UserRole
from app.db.session import commit_or_conflict
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.attendance import AttendanceRecord
from app.models.course_mark import CourseMark
from app.models.exam import Exam
from app.models.enrollment import Enrollment
from app.models.semester import Semester
from app.models.student import Student
from app.schemas.course import CourseCreate, CourseUpdate


def list_courses(db: Session, actor: Student, skip: int, limit: int) -> list[Course]:
    statement = select(Course)
    if actor.role != UserRole.ADMIN.value:
        statement = statement.where((Course.owner_id.is_(None)) | (Course.owner_id == actor.id))
    statement = statement.order_by(Course.id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_course(
    db: Session, course_id: int, student_id: int | None = None, *, allow_foreign_owner: bool = False
) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise NotFoundError("Course not found.")
    if course.owner_id is not None and course.owner_id != student_id and not allow_foreign_owner:
        raise NotFoundError("Course not found.")
    return course


def create_course(db: Session, actor: Student, data: CourseCreate) -> Course:
    semester = _get_semester(db, actor.id, data.semester_id) if data.semester_id else None
    values = data.model_dump(exclude={"semester_id"})
    course = Course(**values, owner_id=actor.id)
    db.add(course)
    if semester is not None:
        db.add(Enrollment(
            student_id=actor.id,
            course=course,
            semester_id=semester.id,
            semester=f"Semester {semester.number}",
            status="enrolled",
        ))
    commit_or_conflict(db, "A course with that code already exists or could not be added to that semester.")
    db.refresh(course)
    return course


def update_course(db: Session, actor: Student, course_id: int, data: CourseUpdate) -> Course:
    course = get_course(db, course_id, actor.id, allow_foreign_owner=actor.role == UserRole.ADMIN.value)
    if course.owner_id != actor.id and actor.role != UserRole.ADMIN.value:
        raise ForbiddenError("Only the course owner or an admin can update this course.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    commit_or_conflict(db, "A course with that code already exists.")
    db.refresh(course)
    return course


def delete_course(db: Session, actor: Student, course_id: int) -> None:
    course = get_course(db, course_id, actor.id, allow_foreign_owner=actor.role == UserRole.ADMIN.value)
    if course.owner_id != actor.id and actor.role != UserRole.ADMIN.value:
        raise ForbiddenError("Only the course owner or an admin can delete this course.")
    dependent_records = (CourseMark, AttendanceRecord, Exam, Assignment)
    if any(db.scalar(select(model.id).where(model.course_id == course.id).limit(1)) for model in dependent_records):
        raise ConflictError("This course has academic records. Delete or preserve those records before removing the course.")
    if course.owner_id == actor.id:
        db.execute(delete(Enrollment).where(Enrollment.course_id == course.id, Enrollment.student_id == actor.id))
    elif actor.role == UserRole.ADMIN.value and course.owner_id is not None:
        db.execute(delete(Enrollment).where(Enrollment.course_id == course.id))
    elif db.scalar(select(Enrollment.id).where(Enrollment.course_id == course.id).limit(1)) is not None:
        raise ConflictError("This shared course is still in use by enrolled students.")
    db.delete(course)
    commit_or_conflict(db, "Course cannot be deleted while enrollments exist.")


def _get_semester(db: Session, student_id: int, semester_id: int) -> Semester:
    semester = db.scalar(
        select(Semester).where(Semester.id == semester_id, Semester.student_id == student_id)
    )
    if semester is None:
        raise NotFoundError("Semester not found.")
    return semester
