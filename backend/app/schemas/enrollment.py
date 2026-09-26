from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import strip_required

EnrollmentStatus = Literal["enrolled", "withdrawn"]


class EnrollmentCreate(BaseModel):
    course_id: int
    semester_id: int | None = None
    status: EnrollmentStatus = "enrolled"
    semester: str = Field(default="Current", min_length=1, max_length=64)

    @field_validator("semester", mode="before")
    @classmethod
    def normalize_semester(cls, value: object) -> object:
        return strip_required(value)


class EnrollmentUpdate(BaseModel):
    status: EnrollmentStatus | None = None
    semester_id: int | None = None
    semester: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("semester", mode="before")
    @classmethod
    def normalize_semester(cls, value: object) -> object:
        return strip_required(value)


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    status: EnrollmentStatus
    semester: str
    semester_id: int | None = None
    created_at: datetime
    updated_at: datetime
