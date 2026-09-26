from enum import StrEnum


class AssessmentType(StrEnum):
    CAT1 = "CAT1"
    CAT2 = "CAT2"
    FAT = "FAT"
    INTERNAL = "INTERNAL"
    LAB = "LAB"
    ASSIGNMENT = "ASSIGNMENT"
    OTHER = "OTHER"


ASSESSMENT_TYPE_VALUES = tuple(member.value for member in AssessmentType)

ASSESSMENT_TYPE_LABELS: dict[AssessmentType, str] = {
    AssessmentType.CAT1: "CAT 1",
    AssessmentType.CAT2: "CAT 2",
    AssessmentType.FAT: "FAT",
    AssessmentType.INTERNAL: "Internal",
    AssessmentType.LAB: "Lab",
    AssessmentType.ASSIGNMENT: "Assignment",
    AssessmentType.OTHER: "Other",
}
