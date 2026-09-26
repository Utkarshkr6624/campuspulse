from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.core.attendance_status import AttendanceStatus
from app.schemas.course_mark import CourseSummary


class AttendanceCreate(BaseModel):
    course_id: int
    attendance_date: date
    status: AttendanceStatus = AttendanceStatus.PRESENT


class AttendanceUpdate(BaseModel):
    attendance_date: date | None = None
    status: AttendanceStatus | None = None


class AttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    attendance_date: date
    status: AttendanceStatus
    created_at: datetime
    updated_at: datetime
    course: CourseSummary


class CourseAttendanceSummary(BaseModel):
    course: CourseSummary
    total_classes: int
    attended_classes: int
    missed_classes: int
    attendance_percentage: float | None
    records: list[AttendanceRead]


class AttendanceOverview(BaseModel):
    total_classes: int
    attended_classes: int
    missed_classes: int
    attendance_percentage: float | None
    courses_tracked: int
    courses: list[CourseAttendanceSummary]
