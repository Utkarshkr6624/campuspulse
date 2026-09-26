from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.document_enums import DocumentCategory, ProcessingStatus
from app.schemas.common import strip_required


class DocumentCreateMeta(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: DocumentCategory = DocumentCategory.GENERAL

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return strip_required(value)

    @field_validator("description", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    original_filename: str
    file_type: str
    file_size: int
    category: DocumentCategory
    uploaded_by: int
    processing_status: ProcessingStatus
    processing_error: str | None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_index: int
    content: str
    page_number: int | None
    created_at: datetime


class DocumentContentRead(BaseModel):
    document: DocumentRead
    chunks: list[DocumentChunkRead]


class DocumentSearchHit(BaseModel):
    document_id: int
    title: str
    category: DocumentCategory
    file_type: str
    page_number: int | None
    snippet: str
    score: float
    matched_in: str


class DocumentSearchResponse(BaseModel):
    query: str
    total: int
    results: list[DocumentSearchHit]
