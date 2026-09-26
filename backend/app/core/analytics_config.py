"""Centralized analytics thresholds and insight vocabularies.

Keep numeric cutoffs here so services and UIs do not scatter magic numbers.
"""

from enum import StrEnum

# Attendance health bands (percentage). CRITICAL < WARNING <= healthy.
ATTENDANCE_WARNING_THRESHOLD = 75.0
ATTENDANCE_HEALTHY_THRESHOLD = 85.0

# Course score attention band (percentage).
LOW_SCORE_THRESHOLD = 60.0
STRONG_SCORE_THRESHOLD = 80.0
ATTENDANCE_NEAR_THRESHOLD_MARGIN = 5.0

# Insight windows.
UPCOMING_EXAM_DAYS = 14
PERFORMANCE_MEANINGFUL_DELTA = 3.0


class AttendanceHealth(StrEnum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class InsightType(StrEnum):
    LOW_ATTENDANCE = "LOW_ATTENDANCE"
    LOW_SCORE = "LOW_SCORE"
    MISSING_ASSESSMENT = "MISSING_ASSESSMENT"
    PERFORMANCE_IMPROVEMENT = "PERFORMANCE_IMPROVEMENT"
    PERFORMANCE_DECLINE = "PERFORMANCE_DECLINE"
    UPCOMING_EXAM = "UPCOMING_EXAM"
    OVERDUE_ASSIGNMENT = "OVERDUE_ASSIGNMENT"


class InsightSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


def attendance_health(percentage: float | None) -> AttendanceHealth:
    if percentage is None:
        return AttendanceHealth.UNKNOWN
    if percentage < ATTENDANCE_WARNING_THRESHOLD:
        return AttendanceHealth.CRITICAL
    if percentage < ATTENDANCE_HEALTHY_THRESHOLD:
        return AttendanceHealth.WARNING
    return AttendanceHealth.HEALTHY
