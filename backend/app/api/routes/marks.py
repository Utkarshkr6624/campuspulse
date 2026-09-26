from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.course_mark import CourseMarkCreate, CourseMarkRead, CourseMarkUpdate, MarksOverview
from app.services import course_mark_service

router = APIRouter(prefix="/marks", tags=["marks"])


@router.get("", response_model=list[CourseMarkRead])
def list_my_marks(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[CourseMarkRead]:
    return [course_mark_service.serialize_mark(mark) for mark in course_mark_service.list_marks(db, student.id)]


@router.get("/overview", response_model=MarksOverview)
def marks_overview(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> MarksOverview:
    return course_mark_service.build_overview(db, student.id)


@router.get("/courses/{course_id}", response_model=list[CourseMarkRead])
def list_marks_for_course(
    course_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[CourseMarkRead]:
    marks = course_mark_service.list_marks_for_course(db, student.id, course_id)
    return [course_mark_service.serialize_mark(mark) for mark in marks]


@router.get("/{mark_id}", response_model=CourseMarkRead)
def get_mark(
    mark_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> CourseMarkRead:
    return course_mark_service.serialize_mark(course_mark_service.get_mark(db, student.id, mark_id))


@router.post("", response_model=CourseMarkRead, status_code=status.HTTP_201_CREATED)
def create_mark(
    data: CourseMarkCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> CourseMarkRead:
    return course_mark_service.serialize_mark(course_mark_service.create_mark(db, student.id, data))


@router.patch("/{mark_id}", response_model=CourseMarkRead)
def update_mark(
    mark_id: int,
    data: CourseMarkUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> CourseMarkRead:
    return course_mark_service.serialize_mark(
        course_mark_service.update_mark(db, student.id, mark_id, data)
    )


@router.delete("/{mark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mark(
    mark_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Response:
    course_mark_service.delete_mark(db, student.id, mark_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
