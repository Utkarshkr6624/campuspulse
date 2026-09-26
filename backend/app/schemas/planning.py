from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.academic import GpaRead
from app.schemas.course_mark import CourseSummary
from app.schemas.common import strip_upper

TargetType = Literal["SGPA", "CGPA"]


class AcademicTargetWrite(BaseModel):
    target_value: float = Field(ge=0, le=10)


class AcademicTargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_type: TargetType
    target_value: float
    current_value: float | None
    status: Literal["INSUFFICIENT_DATA", "IN_PROGRESS", "REACHED"]
    remaining: float | None
    created_at: datetime
    updated_at: datetime


class AssessmentScenarioInput(BaseModel):
    course_id: int
    assessment_type: str = Field(min_length=1, max_length=64)
    marks_obtained: float = Field(ge=0)
    maximum_marks: float = Field(gt=0)

    @field_validator("assessment_type", mode="before")
    @classmethod
    def normalize_assessment_type(cls, value: object) -> object:
        return strip_upper(value)

    @model_validator(mode="after")
    def validate_marks(self):
        if self.marks_obtained > self.maximum_marks:
            raise ValueError("Marks obtained cannot exceed maximum marks.")
        return self


class ScenarioWrite(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    assessments: list[AssessmentScenarioInput] = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_unique_assessments(self):
        keys = [(item.course_id, item.assessment_type) for item in self.assessments]
        if len(keys) != len(set(keys)):
            raise ValueError("A scenario can contain one entry per course and assessment name.")
        return self


class ScenarioUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    assessments: list[AssessmentScenarioInput] | None = Field(default=None, min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_unique_assessments(self):
        if self.assessments is not None:
            keys = [(item.course_id, item.assessment_type) for item in self.assessments]
            if len(keys) != len(set(keys)):
                raise ValueError("A scenario can contain one entry per course and assessment name.")
        return self


class ScenarioPreviewRequest(BaseModel):
    assessments: list[AssessmentScenarioInput] = Field(min_length=1, max_length=100)


class ScenarioCourseResult(BaseModel):
    course: CourseSummary
    current_score: float | None
    projected_score: float | None
    current_grade: str | None
    projected_grade: str | None
    source: Literal["ACTUAL", "SCENARIO"]


class ScenarioProjection(BaseModel):
    current_sgpa: GpaRead
    projected_sgpa: GpaRead
    current_cgpa: GpaRead
    projected_cgpa: GpaRead
    courses: list[ScenarioCourseResult]
    note: str


class ScenarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    assessments: list[AssessmentScenarioInput]
    notes: str | None
    projection: ScenarioProjection
    created_at: datetime
    updated_at: datetime


class ScenarioCompareRequest(BaseModel):
    scenario_ids: list[int] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_ids(self):
        if len(self.scenario_ids) != len(set(self.scenario_ids)):
            raise ValueError("Choose each scenario only once.")
        return self


class ScenarioCompareRead(BaseModel):
    scenarios: list[ScenarioRead]
