from enum import StrEnum


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


ATTENDANCE_STATUS_VALUES = tuple(member.value for member in AttendanceStatus)

# Statuses that count toward "attended" for percentage.
ATTENDED_STATUSES = frozenset(
    {
        AttendanceStatus.PRESENT.value,
        AttendanceStatus.LATE.value,
    }
)

# Statuses that count toward "missed".
MISSED_STATUSES = frozenset({AttendanceStatus.ABSENT.value})
