from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.db.session import commit_or_conflict
from app.models.attendance import AttendanceRecord
from app.models.enrollment import Enrollment
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceOverview,
    AttendanceRead,
    AttendanceUpdate,
    CourseAttendanceSummary,
)
from app.services import course_service
from app.services.academic.attendance_math import summarize_statuses


def list_records(db: Session, student_id: int) -> list[AttendanceRecord]:
    statement = (
        select(AttendanceRecord)
        .where(AttendanceRecord.student_id == student_id)
        .options(joinedload(AttendanceRecord.course))
        .order_by(AttendanceRecord.attendance_date.desc(), AttendanceRecord.id.desc())
    )
    return list(db.scalars(statement).unique().all())


def list_records_for_course(db: Session, student_id: int, course_id: int) -> list[AttendanceRecord]:
    course_service.get_course(db, course_id, student_id)
    statement = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.course_id == course_id,
        )
        .options(joinedload(AttendanceRecord.course))
        .order_by(AttendanceRecord.attendance_date.desc(), AttendanceRecord.id.desc())
    )
    return list(db.scalars(statement).unique().all())


def get_record(db: Session, student_id: int, record_id: int) -> AttendanceRecord:
    statement = (
        select(AttendanceRecord)
        .where(AttendanceRecord.id == record_id, AttendanceRecord.student_id == student_id)
        .options(joinedload(AttendanceRecord.course))
    )
    record = db.scalars(statement).unique().first()
    if record is None:
        raise NotFoundError("Attendance record not found.")
    return record


def create_record(db: Session, student_id: int, data: AttendanceCreate) -> AttendanceRecord:
    course_service.get_course(db, data.course_id, student_id)
    _require_active_enrollment(db, student_id, data.course_id)
    if data.attendance_date > date.today():
        raise BadRequestError("Attendance date cannot be in the future.")
    record = AttendanceRecord(
        student_id=student_id,
        course_id=data.course_id,
        attendance_date=data.attendance_date,
        status=data.status.value,
    )
    db.add(record)
    commit_or_conflict(db, "Attendance for that course and date already exists.")
    return get_record(db, student_id, record.id)


def update_record(
    db: Session,
    student_id: int,
    record_id: int,
    data: AttendanceUpdate,
) -> AttendanceRecord:
    record = get_record(db, student_id, record_id)
    changes = data.model_dump(exclude_unset=True)
    if "status" in changes and changes["status"] is not None:
        changes["status"] = changes["status"].value
    if "attendance_date" in changes and changes["attendance_date"] is not None:
        if changes["attendance_date"] > date.today():
            raise BadRequestError("Attendance date cannot be in the future.")
    for field, value in changes.items():
        setattr(record, field, value)
    commit_or_conflict(db, "Attendance for that course and date already exists.")
    return get_record(db, student_id, record.id)


def delete_record(db: Session, student_id: int, record_id: int) -> None:
    record = get_record(db, student_id, record_id)
    db.delete(record)
    commit_or_conflict(db, "Attendance record could not be deleted.")


def build_overview(db: Session, student_id: int) -> AttendanceOverview:
    records = list_records(db, student_id)
    grouped: dict[int, list[AttendanceRecord]] = defaultdict(list)
    for record in records:
        grouped[record.course_id].append(record)

    courses: list[CourseAttendanceSummary] = []
    all_statuses: list[str] = []
    for course_records in grouped.values():
        statuses = [item.status for item in course_records]
        all_statuses.extend(statuses)
        summary = summarize_statuses(statuses)
        courses.append(
            CourseAttendanceSummary(
                course=course_records[0].course,
                total_classes=summary["total_classes"],
                attended_classes=summary["attended_classes"],
                missed_classes=summary["missed_classes"],
                attendance_percentage=summary["attendance_percentage"],
                records=[serialize_record(item) for item in course_records],
            )
        )
    courses.sort(key=lambda item: item.course.code)
    overall = summarize_statuses(all_statuses)
    return AttendanceOverview(
        total_classes=overall["total_classes"],
        attended_classes=overall["attended_classes"],
        missed_classes=overall["missed_classes"],
        attendance_percentage=overall["attendance_percentage"],
        courses_tracked=len(courses),
        courses=courses,
    )


def course_summary(db: Session, student_id: int, course_id: int) -> CourseAttendanceSummary:
    records = list_records_for_course(db, student_id, course_id)
    course = course_service.get_course(db, course_id, student_id)
    statuses = [item.status for item in records]
    summary = summarize_statuses(statuses)
    return CourseAttendanceSummary(
        course=course,
        total_classes=summary["total_classes"],
        attended_classes=summary["attended_classes"],
        missed_classes=summary["missed_classes"],
        attendance_percentage=summary["attendance_percentage"],
        records=[serialize_record(item) for item in records],
    )


def serialize_record(record: AttendanceRecord) -> AttendanceRead:
    return AttendanceRead(
        id=record.id,
        student_id=record.student_id,
        course_id=record.course_id,
        attendance_date=record.attendance_date,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        course=record.course,
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
        raise ConflictError("Enroll in the course before recording attendance.")
