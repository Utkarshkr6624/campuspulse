from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import strip_required, strip_upper


class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=200)
    credits: int = Field(ge=1, le=40)
    grading_scheme_id: int | None = None
    semester_id: int | None = None

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        return strip_upper(value)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return strip_required(value)


class CourseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=32)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    credits: int | None = Field(default=None, ge=1, le=40)
    grading_scheme_id: int | None = None

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        return strip_upper(value)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return strip_required(value)


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    credits: int
    grading_scheme_id: int | None
    owner_id: int | None = None
    created_at: datetime
    updated_at: datetime
