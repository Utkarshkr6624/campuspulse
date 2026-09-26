from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import strip_upper


class CourseMarkCreate(BaseModel):
    course_id: int
    assessment_type: str = Field(min_length=1, max_length=64)
    marks_obtained: float = Field(ge=0)
    maximum_marks: float = Field(gt=0)
    assessment_date: date | None = None

    @model_validator(mode="after")
    def validate_score_range(self) -> "CourseMarkCreate":
        if self.marks_obtained > self.maximum_marks:
            raise ValueError("marks_obtained cannot exceed maximum_marks")
        return self

    @field_validator("assessment_type", mode="before")
    @classmethod
    def normalize_assessment_type(cls, value: object) -> object:
        return strip_upper(value)


class CourseMarkUpdate(BaseModel):
    assessment_type: str | None = Field(default=None, min_length=1, max_length=64)
    marks_obtained: float | None = Field(default=None, ge=0)
    maximum_marks: float | None = Field(default=None, gt=0)
    assessment_date: date | None = None

    @field_validator("assessment_date", mode="before")
    @classmethod
    def keep_explicit_null(cls, value: object) -> object:
        return value

    @field_validator("assessment_type", mode="before")
    @classmethod
    def normalize_assessment_type(cls, value: object) -> object:
        return strip_upper(value) if value is not None else None


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    credits: int


class CourseMarkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    assessment_type: str
    marks_obtained: float
    maximum_marks: float
    assessment_date: date | None
    created_at: datetime
    updated_at: datetime
    course: CourseSummary
    percentage: float


class CourseMarksGroup(BaseModel):
    course: CourseSummary
    assessments: list[CourseMarkRead]
    assessment_count: int
    average_percentage: float | None


class MarksOverview(BaseModel):
    total_assessments: int
    courses_with_marks: int
    average_percentage: float | None
    groups: list[CourseMarksGroup]
