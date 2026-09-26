"""Centralized document categories, processing statuses, and file rules."""

from enum import StrEnum

# 10 MiB default upload ceiling.
DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class DocumentCategory(StrEnum):
    ACADEMIC = "ACADEMIC"
    EXAMINATION = "EXAMINATION"
    ATTENDANCE = "ATTENDANCE"
    FEES = "FEES"
    HOSTEL = "HOSTEL"
    PLACEMENT = "PLACEMENT"
    GENERAL = "GENERAL"
    OTHER = "OTHER"


class ProcessingStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


DOCUMENT_CATEGORY_VALUES = tuple(member.value for member in DocumentCategory)
PROCESSING_STATUS_VALUES = tuple(member.value for member in ProcessingStatus)

DOCUMENT_CATEGORY_LABELS: dict[DocumentCategory, str] = {
    DocumentCategory.ACADEMIC: "Academic",
    DocumentCategory.EXAMINATION: "Examination",
    DocumentCategory.ATTENDANCE: "Attendance",
    DocumentCategory.FEES: "Fees",
    DocumentCategory.HOSTEL: "Hostel",
    DocumentCategory.PLACEMENT: "Placement",
    DocumentCategory.GENERAL: "General",
    DocumentCategory.OTHER: "Other",
}

# Extension → canonical file type label used in the database.
ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "PDF",
    ".txt": "TXT",
    ".docx": "DOCX",
}

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",  # browsers sometimes send this; extension still required
    }
)
