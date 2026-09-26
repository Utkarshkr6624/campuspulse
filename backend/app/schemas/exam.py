from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.exam_types import ExamType
from app.schemas.common import strip_required
from app.schemas.course_mark import CourseSummary


class ExamCreate(BaseModel):
    course_id: int
    title: str = Field(min_length=1, max_length=200)
    exam_type: ExamType
    exam_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(default=None, max_length=200)
    description: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return strip_required(value)

    @field_validator("location", "description", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_times(self) -> "ExamCreate":
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ExamUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    exam_type: ExamType | None = None
    exam_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(default=None, max_length=200)
    description: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return strip_required(value)

    @field_validator("location", "description", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class ExamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    title: str
    exam_type: ExamType
    exam_date: date
    start_time: time | None
    end_time: time | None
    location: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime
    course: CourseSummary
    is_upcoming: bool
    days_until: int
