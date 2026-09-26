from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.db.session import commit_or_conflict
from app.models.course_mark import CourseMark
from app.models.enrollment import Enrollment
from app.schemas.course_mark import (
    CourseMarkCreate,
    CourseMarkRead,
    CourseMarkUpdate,
    CourseMarksGroup,
    MarksOverview,
)
from app.services import course_service
from app.services.academic import assessment_percentage


def list_marks(db: Session, student_id: int) -> list[CourseMark]:
    statement = (
        select(CourseMark)
        .where(CourseMark.student_id == student_id)
        .options(joinedload(CourseMark.course))
        .order_by(CourseMark.course_id, CourseMark.assessment_type, CourseMark.id)
    )
    return list(db.scalars(statement).unique().all())


def list_marks_for_course(db: Session, student_id: int, course_id: int) -> list[CourseMark]:
    course_service.get_course(db, course_id, student_id)
    statement = (
        select(CourseMark)
        .where(CourseMark.student_id == student_id, CourseMark.course_id == course_id)
        .options(joinedload(CourseMark.course))
        .order_by(CourseMark.assessment_type, CourseMark.id)
    )
    return list(db.scalars(statement).unique().all())


def get_mark(db: Session, student_id: int, mark_id: int) -> CourseMark:
    statement = (
        select(CourseMark)
        .where(CourseMark.id == mark_id, CourseMark.student_id == student_id)
        .options(joinedload(CourseMark.course))
    )
    mark = db.scalars(statement).unique().first()
    if mark is None:
        raise NotFoundError("Mark not found.")
    return mark


def create_mark(db: Session, student_id: int, data: CourseMarkCreate) -> CourseMark:
    course_service.get_course(db, data.course_id, student_id)
    _require_active_enrollment(db, student_id, data.course_id)
    mark = CourseMark(
        student_id=student_id,
        course_id=data.course_id,
        assessment_type=data.assessment_type,
        marks_obtained=data.marks_obtained,
        maximum_marks=data.maximum_marks,
        assessment_date=data.assessment_date,
    )
    db.add(mark)
    commit_or_conflict(
        db,
        "That assessment already exists for this course. Edit the existing mark instead.",
    )
    return get_mark(db, student_id, mark.id)


def update_mark(db: Session, student_id: int, mark_id: int, data: CourseMarkUpdate) -> CourseMark:
    mark = get_mark(db, student_id, mark_id)
    changes = data.model_dump(exclude_unset=True)
    if "assessment_type" in changes and changes["assessment_type"] is not None:
        changes["assessment_type"] = changes["assessment_type"]

    next_obtained = changes.get("marks_obtained", mark.marks_obtained)
    next_maximum = changes.get("maximum_marks", mark.maximum_marks)
    if next_obtained > next_maximum:
        raise BadRequestError("marks_obtained cannot exceed maximum_marks.")

    for field, value in changes.items():
        setattr(mark, field, value)
    commit_or_conflict(
        db,
        "That assessment already exists for this course. Edit the existing mark instead.",
    )
    return get_mark(db, student_id, mark.id)


def delete_mark(db: Session, student_id: int, mark_id: int) -> None:
    mark = get_mark(db, student_id, mark_id)
    db.delete(mark)
    commit_or_conflict(db, "Mark could not be deleted.")


def build_overview(db: Session, student_id: int) -> MarksOverview:
    marks = list_marks(db, student_id)
    reads = [serialize_mark(mark) for mark in marks]
    grouped: dict[int, list[CourseMarkRead]] = defaultdict(list)
    for item in reads:
        grouped[item.course_id].append(item)

    groups: list[CourseMarksGroup] = []
    for course_marks in grouped.values():
        percentages = [item.percentage for item in course_marks]
        groups.append(
            CourseMarksGroup(
                course=course_marks[0].course,
                assessments=course_marks,
                assessment_count=len(course_marks),
                average_percentage=round(sum(percentages) / len(percentages), 2) if percentages else None,
            )
        )
    groups.sort(key=lambda group: group.course.code)

    all_percentages = [item.percentage for item in reads]
    return MarksOverview(
        total_assessments=len(reads),
        courses_with_marks=len(groups),
        average_percentage=round(sum(all_percentages) / len(all_percentages), 2) if all_percentages else None,
        groups=groups,
    )


def serialize_mark(mark: CourseMark) -> CourseMarkRead:
    return CourseMarkRead(
        id=mark.id,
        student_id=mark.student_id,
        course_id=mark.course_id,
        assessment_type=mark.assessment_type,
        marks_obtained=mark.marks_obtained,
        maximum_marks=mark.maximum_marks,
        assessment_date=mark.assessment_date,
        created_at=mark.created_at,
        updated_at=mark.updated_at,
        course=mark.course,
        percentage=assessment_percentage(mark.marks_obtained, mark.maximum_marks),
    )


def _require_active_enrollment(db: Session, student_id: int, course_id: int) -> None:
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
            Enrollment.status == "enrolled",
        )
    )
    if enrollment is None:
        raise ConflictError("Enroll in the course before adding marks.")
