"""Attendance percentage helpers."""

from app.core.attendance_status import ATTENDED_STATUSES, MISSED_STATUSES


def attendance_percentage(attended: int, total: int) -> float | None:
    if total < 0 or attended < 0:
        raise ValueError("Attendance counts cannot be negative.")
    if attended > total:
        raise ValueError("Attended classes cannot exceed total classes.")
    if total == 0:
        return None
    return round((attended / total) * 100, 2)


def summarize_statuses(statuses: list[str]) -> dict[str, int | float | None]:
    total = len(statuses)
    attended = sum(1 for status in statuses if status in ATTENDED_STATUSES)
    missed = sum(1 for status in statuses if status in MISSED_STATUSES)
    return {
        "total_classes": total,
        "attended_classes": attended,
        "missed_classes": missed,
        "attendance_percentage": attendance_percentage(attended, total),
    }
