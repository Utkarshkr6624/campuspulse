from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.assignment_enums import AssignmentPriority, AssignmentStatus
from app.schemas.common import strip_required
from app.schemas.course_mark import CourseSummary


class AssignmentCreate(BaseModel):
    course_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_date: date
    due_time: time | None = None
    status: AssignmentStatus = AssignmentStatus.TODO
    priority: AssignmentPriority = AssignmentPriority.MEDIUM

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return strip_required(value)

    @field_validator("description", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    status: AssignmentStatus | None = None
    priority: AssignmentPriority | None = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return strip_required(value)

    @field_validator("description", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    title: str
    description: str | None
    due_date: date
    due_time: time | None
    status: AssignmentStatus
    priority: AssignmentPriority
    created_at: datetime
    updated_at: datetime
    course: CourseSummary
    is_overdue: bool
    is_due_today: bool
    days_until: int
