from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import normalize_email, strip_required, strip_upper


class StudentCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    university_id: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: object) -> object:
        return strip_required(value)

    @field_validator("university_id", mode="before")
    @classmethod
    def normalize_university_id(cls, value: object) -> object:
        return strip_upper(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_student_email(cls, value: object) -> object:
        return normalize_email(value)


class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    university_id: str | None = Field(default=None, min_length=1, max_length=32)

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: object) -> object:
        return strip_required(value)

    @field_validator("university_id", mode="before")
    @classmethod
    def normalize_university_id(cls, value: object) -> object:
        return strip_upper(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_student_email(cls, value: object) -> object:
        return normalize_email(value)


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    university_id: str
    role: str
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_login_email(cls, value: object) -> object:
        return normalize_email(value)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentRead
