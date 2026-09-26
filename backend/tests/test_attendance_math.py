import pytest

from app.services.academic.attendance_math import attendance_percentage, summarize_statuses


def test_attendance_percentage_basic():
    assert attendance_percentage(42, 50) == 84.0


def test_attendance_percentage_zero_classes():
    assert attendance_percentage(0, 0) is None


def test_attendance_percentage_rejects_invalid():
    with pytest.raises(ValueError):
        attendance_percentage(5, 4)
    with pytest.raises(ValueError):
        attendance_percentage(-1, 4)


def test_summarize_statuses():
    summary = summarize_statuses(["present", "absent", "late", "excused", "present"])
    assert summary["total_classes"] == 5
    assert summary["attended_classes"] == 3
    assert summary["missed_classes"] == 1
    assert summary["attendance_percentage"] == 60.0
