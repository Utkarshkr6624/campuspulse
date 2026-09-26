from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.roles import UserRole
from app.core.security import read_student_id
from app.db.session import get_db
from app.models.student import Student

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_student(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Student:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Authentication is required.")
    student_id = read_student_id(credentials.credentials)
    student = db.get(Student, student_id)
    if student is None:
        raise UnauthorizedError("Invalid authentication token.")
    return student


def get_current_admin(student: Student = Depends(get_current_student)) -> Student:
    if student.role != UserRole.ADMIN.value:
        raise ForbiddenError("Admin privileges are required for this action.")
    return student
