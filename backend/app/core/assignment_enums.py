from enum import StrEnum


class AssignmentStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class AssignmentPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


ASSIGNMENT_STATUS_VALUES = tuple(member.value for member in AssignmentStatus)
ASSIGNMENT_PRIORITY_VALUES = tuple(member.value for member in AssignmentPriority)

ASSIGNMENT_STATUS_LABELS: dict[AssignmentStatus, str] = {
    AssignmentStatus.TODO: "To do",
    AssignmentStatus.IN_PROGRESS: "In progress",
    AssignmentStatus.COMPLETED: "Completed",
}

ASSIGNMENT_PRIORITY_LABELS: dict[AssignmentPriority, str] = {
    AssignmentPriority.LOW: "Low",
    AssignmentPriority.MEDIUM: "Medium",
    AssignmentPriority.HIGH: "High",
}
