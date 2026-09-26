from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_student
from app.db.session import get_db
from app.models.student import Student
from app.schemas.student import AuthResponse, LoginRequest, StudentCreate, StudentRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(data: StudentCreate, db: Session = Depends(get_db)) -> AuthResponse:
    return auth_service.register_student(db, data)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return auth_service.login_student(db, data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_student: Student = Depends(get_current_student)) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=StudentRead)
def current_student(student: Student = Depends(get_current_student)) -> Student:
    return student
