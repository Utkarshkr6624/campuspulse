from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["courses"], dependencies=[Depends(get_current_student)])


@router.get("", response_model=list[CourseRead])
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CourseRead]:
    return course_service.list_courses(db, skip, limit)


@router.get("/{course_id}", response_model=CourseRead)
def get_course(course_id: int, db: Session = Depends(get_db)) -> CourseRead:
    return course_service.get_course(db, course_id)


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, db: Session = Depends(get_db)) -> CourseRead:
    return course_service.create_course(db, data)


@router.patch("/{course_id}", response_model=CourseRead)
def update_course(
    course_id: int,
    data: CourseUpdate,
    db: Session = Depends(get_db),
) -> CourseRead:
    return course_service.update_course(db, course_id, data)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(get_db)) -> Response:
    course_service.delete_course(db, course_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
