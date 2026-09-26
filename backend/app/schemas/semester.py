from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.academic import GpaRead

SemesterStatus = Literal["PREVIOUS", "CURRENT", "UPCOMING"]
CourseComponent = Literal["THEORY", "LAB", "COMBINED", "OTHER"]


class SemesterSetup(BaseModel):
    current_semester: int = Field(ge=1, le=100)


class SemesterCreate(BaseModel):
    number: int = Field(ge=1, le=100)
    set_current: bool = False


class SemesterCourseCreate(BaseModel):
    course_id: int | None = None
    course_name: str = Field(min_length=1, max_length=200)
    course_code: str | None = Field(default=None, max_length=32)
    credits: int = Field(ge=1, le=40)
    grade: str | None = Field(default=None, min_length=1, max_length=8)
    final_score: float | None = Field(default=None, ge=0, le=100)
    course_component: CourseComponent | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_grade_or_score(self):
        if self.grade is None and self.final_score is None:
            raise ValueError("Enter a grade or final score.")
        if self.course_id is None and not self.course_name.strip():
            raise ValueError("Enter a course name.")
        if self.course_code is not None:
            self.course_code = self.course_code.strip().upper() or None
        self.course_name = self.course_name.strip()
        if self.grade is not None:
            self.grade = self.grade.strip().upper()
        return self


class SemesterCourseRead(BaseModel):
    id: int
    course_id: int | None
    course_name: str
    course_code: str | None
    credits: int
    grade: str
    grade_point: float
    final_score: float | None
    course_component: str | None
    notes: str | None


class SemesterRead(BaseModel):
    id: int
    number: int
    status: SemesterStatus
    is_current: bool
    course_count: int
    total_credits: int
    gpa: GpaRead
    created_at: datetime
    updated_at: datetime


class SemesterDetail(SemesterRead):
    historical_courses: list[SemesterCourseRead]
    enrolled_courses: list[dict]


class SemesterHistoryCreate(BaseModel):
    courses: list[SemesterCourseCreate] = Field(min_length=1, max_length=100)
