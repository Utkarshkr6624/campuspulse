"""Letter-grade and grade-point mapping from course scores."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GradeBandRule:
    letter: str
    min_score: float
    max_score: float
    grade_point: float


@dataclass(frozen=True)
class GradeResult:
    letter: str
    grade_point: float


def score_to_letter(score: float, bands: list[GradeBandRule]) -> str:
    if not bands:
        raise ValueError("At least one grade band is required.")
    ordered = sorted(bands, key=lambda band: band.min_score, reverse=True)
    for index, band in enumerate(ordered):
        is_top = index == 0
        if is_top and band.min_score <= score <= band.max_score:
            return band.letter
        if not is_top and band.min_score <= score < band.max_score:
            return band.letter
    # Fallback to lowest band for out-of-range low scores after rounding.
    return ordered[-1].letter


def letter_to_grade_point(letter: str, bands: list[GradeBandRule]) -> float:
    for band in bands:
        if band.letter == letter:
            return band.grade_point
    raise ValueError(f"Unknown letter grade: {letter}")


def compute_grade(score: float, bands: list[GradeBandRule]) -> GradeResult:
    letter = score_to_letter(score, bands)
    return GradeResult(letter=letter, grade_point=letter_to_grade_point(letter, bands))
