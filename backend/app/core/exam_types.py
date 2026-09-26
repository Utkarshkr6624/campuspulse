from enum import StrEnum


class ExamType(StrEnum):
    CAT1 = "CAT1"
    CAT2 = "CAT2"
    FAT = "FAT"
    QUIZ = "QUIZ"
    LAB = "LAB"
    OTHER = "OTHER"


EXAM_TYPE_VALUES = tuple(member.value for member in ExamType)

EXAM_TYPE_LABELS: dict[ExamType, str] = {
    ExamType.CAT1: "CAT 1",
    ExamType.CAT2: "CAT 2",
    ExamType.FAT: "FAT",
    ExamType.QUIZ: "Quiz",
    ExamType.LAB: "Lab",
    ExamType.OTHER: "Other",
}
