from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.db.session import commit_or_conflict
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.semester import Semester, SemesterCourse
from app.schemas.academic import GpaRead
from app.schemas.semester import (
    SemesterCourseCreate,
    SemesterCourseRead,
    SemesterDetail,
    SemesterRead,
    SemesterSetup,
    SemesterCreate,
)
from app.services import academic_service, grading_scheme_service
from app.services.academic import GradedCourseInput, GradeBandRule, compute_gpa, compute_grade, letter_to_grade_point


def list_semesters(db: Session, student_id: int) -> list[SemesterRead]:
    rows = db.scalars(
        select(Semester).where(Semester.student_id == student_id).order_by(Semester.number)
    ).all()
    return [_summary(db, row) for row in rows]


def get_semester(db: Session, student_id: int, semester_id: int) -> Semester:
    row = db.scalar(
        select(Semester)
        .where(Semester.id == semester_id, Semester.student_id == student_id)
        .options(joinedload(Semester.history_courses))
    )
    if row is None:
        raise NotFoundError("Semester not found.")
    return row


def get_semester_detail(db: Session, student_id: int, semester_id: int) -> SemesterDetail:
    semester = get_semester(db, student_id, semester_id)
    summary = _summary(db, semester)
    enrolled_courses = [
        item.model_dump()
        for item in academic_service.list_course_performance(
            db, student_id, semester_id=semester.id
        )
    ]
    return SemesterDetail(
        **summary.model_dump(),
        historical_courses=[_course_read(item) for item in semester.history_courses],
        enrolled_courses=enrolled_courses,
    )


def setup_semesters(db: Session, student_id: int, data: SemesterSetup) -> list[SemesterRead]:
    rows = list(db.scalars(select(Semester).where(Semester.student_id == student_id)).all())
    by_number = {row.number: row for row in rows}
    for number in range(1, data.current_semester + 1):
        if number not in by_number:
            row = Semester(student_id=student_id, number=number, is_current=False)
            db.add(row)
            by_number[number] = row
    db.flush()
    db.execute(update(Semester).where(Semester.student_id == student_id).values(is_current=False))
    by_number[data.current_semester].is_current = True
    _attach_unassigned_enrollments(db, student_id, by_number[data.current_semester].id)
    commit_or_conflict(db, "Semester setup could not be saved.")
    return list_semesters(db, student_id)


def create_semester(db: Session, student_id: int, data: SemesterCreate) -> SemesterRead:
    if db.scalar(select(Semester.id).where(Semester.student_id == student_id, Semester.number == data.number)):
        raise ConflictError("That semester already exists.")
    if data.set_current:
        db.execute(update(Semester).where(Semester.student_id == student_id).values(is_current=False))
    semester = Semester(student_id=student_id, number=data.number, is_current=data.set_current)
    db.add(semester)
    commit_or_conflict(db, "That semester already exists.")
    db.refresh(semester)
    if data.set_current:
        _attach_unassigned_enrollments(db, student_id, semester.id)
        db.commit()
    return _summary(db, semester)


def set_current_semester(db: Session, student_id: int, semester_id: int) -> list[SemesterRead]:
    selected = get_semester(db, student_id, semester_id)
    if selected.history_courses:
        raise ConflictError("This semester contains historical grade records and cannot be made current.")
    db.execute(update(Semester).where(Semester.student_id == student_id).values(is_current=False))
    selected.is_current = True
    _attach_unassigned_enrollments(db, student_id, selected.id)
    commit_or_conflict(db, "Current semester could not be changed.")
    return list_semesters(db, student_id)


def delete_semester(db: Session, student_id: int, semester_id: int) -> None:
    semester = get_semester(db, student_id, semester_id)
    if semester.is_current:
        raise BadRequestError("Choose another current semester before deleting this one.")
    if semester.history_courses or db.scalar(
        select(Enrollment.id).where(Enrollment.semester_id == semester.id).limit(1)
    ):
        raise ConflictError("This semester contains academic records and cannot be deleted.")
    db.delete(semester)
    commit_or_conflict(db, "Semester could not be deleted.")


def add_history_course(
    db: Session, student_id: int, semester_id: int, data: SemesterCourseCreate
) -> SemesterCourseRead:
    semester = get_semester(db, student_id, semester_id)
    current_number = db.scalar(
        select(Semester.number).where(Semester.student_id == student_id, Semester.is_current.is_(True))
    )
    if current_number is None or semester.number >= current_number:
        raise BadRequestError("Historical course results can only be added to a previous semester.")
    course = db.get(Course, data.course_id) if data.course_id is not None else None
    if data.course_id is not None and course is None:
        raise NotFoundError("Course not found.")
    name = course.title if course else data.course_name
    code = course.code if course else data.course_code
    if code and db.scalar(
        select(SemesterCourse.id).where(
            SemesterCourse.semester_id == semester.id,
            SemesterCourse.course_code == code,
        )
    ):
        raise ConflictError("A course with that code already exists in this semester.")

    scheme = grading_scheme_service.resolve_scheme_for_course(db, course.grading_scheme_id if course else None)
    bands = [GradeBandRule(b.letter, b.min_score, b.max_score, b.grade_point) for b in scheme.grade_bands]
    if data.final_score is not None:
        derived = compute_grade(data.final_score, bands)
        if data.grade is not None and data.grade != derived.letter:
            raise BadRequestError("The entered grade does not match the configured grade band for this score.")
        grade, point = derived.letter, derived.grade_point
    else:
        grade = data.grade or ""
        try:
            point = letter_to_grade_point(grade, bands)
        except ValueError:
            raise BadRequestError("Choose a grade from the configured grading scheme.") from None

    record = SemesterCourse(
        semester_id=semester.id,
        course_id=course.id if course else None,
        course_name=name,
        course_code=code,
        credits=data.credits,
        grade=grade,
        grade_point=point,
        final_score=data.final_score,
        course_component=data.course_component,
        notes=data.notes,
    )
    db.add(record)
    commit_or_conflict(db, "A course with that code already exists in this semester.")
    db.refresh(record)
    return _course_read(record)


def update_history_course(
    db: Session,
    student_id: int,
    semester_id: int,
    record_id: int,
    data: SemesterCourseCreate,
) -> SemesterCourseRead:
    record = _get_history_course(db, student_id, semester_id, record_id)
    db.delete(record)
    db.flush()
    return add_history_course(db, student_id, semester_id, data)


def delete_history_course(db: Session, student_id: int, semester_id: int, record_id: int) -> None:
    db.delete(_get_history_course(db, student_id, semester_id, record_id))
    commit_or_conflict(db, "Course history could not be deleted.")


def cumulative_gpa(db: Session, student_id: int) -> GpaRead:
    semesters = list(db.scalars(select(Semester).where(Semester.student_id == student_id)).all())
    graded: list[GradedCourseInput] = []
    current = next((item for item in semesters if item.is_current), None)
    if current is None:
        legacy = academic_service.list_course_performance(db, student_id)
        result = compute_gpa([
            GradedCourseInput(item.course.id, item.credits, item.grade_point or 0, item.status)
            for item in legacy
        ])
        return GpaRead(
            status=result.status,
            value=result.value,
            credited_courses=result.credited_courses,
            total_credits=result.total_credits,
            semester=None,
            message=result.message,
        )
    current_number = current.number if current is not None else None
    for semester in semesters:
        if current_number is not None and semester.number >= current_number:
            continue
        history_codes = {item.course_code for item in semester.history_courses if item.course_code}
        for item in semester.history_courses:
            graded.append(GradedCourseInput(item.id, item.credits, item.grade_point, "complete"))
        for performance in academic_service.list_course_performance(
            db, student_id, semester_id=semester.id
        ):
            if performance.course.code not in history_codes:
                graded.append(
                    GradedCourseInput(
                        performance.course.id,
                        performance.credits,
                        performance.grade_point or 0,
                        performance.status,
                    )
                )
    if current is not None:
        for performance in academic_service.list_course_performance(
            db, student_id, semester_id=current.id
        ):
            graded.append(
                GradedCourseInput(
                    performance.course.id,
                    performance.credits,
                    performance.grade_point or 0,
                    performance.status,
                )
            )
    result = compute_gpa(graded)
    return GpaRead(
        status=result.status,
        value=result.value,
        credited_courses=result.credited_courses,
        total_credits=result.total_credits,
        semester=None,
        message=result.message,
    )


def _summary(db: Session, semester: Semester) -> SemesterRead:
    history = semester.history_courses
    semester_performances = academic_service.list_course_performance(
        db, semester.student_id, semester_id=semester.id
    )
    history_codes = {item.course_code for item in history if item.course_code}
    semester_performances = [
        item for item in semester_performances if item.course.code not in history_codes
    ]
    gpa_inputs = [
        GradedCourseInput(item.id, item.credits, item.grade_point, "complete") for item in history
    ]
    gpa_inputs.extend(
        GradedCourseInput(item.course.id, item.credits, item.grade_point or 0, item.status)
        for item in semester_performances
    )
    result = compute_gpa(gpa_inputs)
    gpa = GpaRead(
        status=result.status,
        value=result.value,
        credited_courses=result.credited_courses,
        total_credits=result.total_credits,
        semester=f"Semester {semester.number}",
        message=result.message,
    )
    current_number = db.scalar(
        select(Semester.number).where(Semester.student_id == semester.student_id, Semester.is_current.is_(True))
    )
    status = "CURRENT" if semester.is_current else (
        "PREVIOUS" if current_number is not None and semester.number < current_number else "UPCOMING"
    )
    return SemesterRead(
        id=semester.id,
        number=semester.number,
        status=status,
        is_current=semester.is_current,
        course_count=len(history) + len(semester_performances),
        total_credits=sum(item.credits for item in history) + sum(item.credits for item in semester_performances),
        gpa=gpa,
        created_at=semester.created_at,
        updated_at=semester.updated_at,
    )


def _get_history_course(db: Session, student_id: int, semester_id: int, record_id: int) -> SemesterCourse:
    record = db.scalar(
        select(SemesterCourse)
        .join(Semester)
        .where(
            SemesterCourse.id == record_id,
            SemesterCourse.semester_id == semester_id,
            Semester.student_id == student_id,
        )
    )
    if record is None:
        raise NotFoundError("Semester course not found.")
    return record


def _attach_unassigned_enrollments(db: Session, student_id: int, semester_id: int) -> None:
    for enrollment in db.scalars(
        select(Enrollment).where(
            Enrollment.student_id == student_id, Enrollment.semester_id.is_(None)
        )
    ):
        enrollment.semester_id = semester_id


def _course_read(record: SemesterCourse) -> SemesterCourseRead:
    return SemesterCourseRead(
        id=record.id,
        course_id=record.course_id,
        course_name=record.course_name,
        course_code=record.course_code,
        credits=record.credits,
        grade=record.grade,
        grade_point=record.grade_point,
        final_score=record.final_score,
        course_component=record.course_component,
        notes=record.notes,
    )
