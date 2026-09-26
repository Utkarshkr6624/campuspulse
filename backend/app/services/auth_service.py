from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.models.student import Student
from app.schemas.student import AuthResponse, LoginRequest, StudentCreate
from app.services import student_service


def register_student(db: Session, data: StudentCreate) -> AuthResponse:
    student = student_service.create_student(db, data)
    return _auth_response(student)


def login_student(db: Session, data: LoginRequest) -> AuthResponse:
    student = student_service.get_student_by_email(db, str(data.email))
    if student is None or not verify_password(data.password, student.password_hash):
        raise UnauthorizedError("Invalid email or password.")
    return _auth_response(student)


def _auth_response(student: Student) -> AuthResponse:
    return AuthResponse(access_token=create_access_token(student.id), student=student)
