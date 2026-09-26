"""Assessment-level calculations from raw marks."""


def assessment_percentage(marks_obtained: float, maximum_marks: float) -> float:
    if maximum_marks <= 0:
        raise ValueError("maximum_marks must be greater than zero")
    if marks_obtained < 0:
        raise ValueError("marks_obtained cannot be negative")
    if marks_obtained > maximum_marks:
        raise ValueError("marks_obtained cannot exceed maximum_marks")
    return round((marks_obtained / maximum_marks) * 100, 2)


def normalize_assessment(marks_obtained: float, maximum_marks: float) -> float:
    """Return a 0–1 ratio for weighting."""
    return assessment_percentage(marks_obtained, maximum_marks) / 100.0
