"""Document upload, processing, and library management."""

from __future__ import annotations

import uuid
import logging
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.document_enums import ALLOWED_EXTENSIONS, DocumentCategory, ProcessingStatus
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.roles import UserRole
from app.db.session import commit_or_conflict
from app.models.document import Document, DocumentChunk
from app.models.student import Student
from app.schemas.document import (
    DocumentContentRead,
    DocumentCreateMeta,
    DocumentChunkRead,
    DocumentRead,
)
from app.services import document_chunker, document_extractor
from app.services.document_extractor import ExtractionError
from app.storage import get_storage

logger = logging.getLogger(__name__)


def list_documents(
    db: Session,
    *,
    category: DocumentCategory | None = None,
    status: ProcessingStatus | None = None,
) -> list[DocumentRead]:
    statement = select(Document).order_by(Document.created_at.desc(), Document.id.desc())
    if category is not None:
        statement = statement.where(Document.category == category.value)
    if status is not None:
        statement = statement.where(Document.processing_status == status.value)
    documents = list(db.scalars(statement).all())
    counts = _chunk_counts(db, [item.id for item in documents])
    return [serialize_document(item, chunk_count=counts.get(item.id, 0)) for item in documents]


def get_document(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError("Document not found.")
    return document


def get_document_read(db: Session, document_id: int) -> DocumentRead:
    document = get_document(db, document_id)
    counts = _chunk_counts(db, [document.id])
    return serialize_document(document, chunk_count=counts.get(document.id, 0))


def get_document_content(db: Session, document_id: int) -> DocumentContentRead:
    statement = (
        select(Document)
        .where(Document.id == document_id)
        .options(joinedload(Document.chunks))
    )
    document = db.scalars(statement).unique().first()
    if document is None:
        raise NotFoundError("Document not found.")
    return DocumentContentRead(
        document=serialize_document(document, chunk_count=len(document.chunks)),
        chunks=[
            DocumentChunkRead(
                id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                created_at=chunk.created_at,
            )
            for chunk in document.chunks
        ],
    )


def upload_document(
    db: Session,
    uploader: Student,
    *,
    meta: DocumentCreateMeta,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> DocumentRead:
    require_admin(uploader)
    if not data:
        raise BadRequestError("Uploaded file is empty.")
    if len(data) > settings.document_max_upload_bytes:
        raise BadRequestError(
            f"File exceeds the maximum size of {settings.document_max_upload_bytes} bytes."
        )

    extension, file_type = _validate_filename(filename)
    # Prefer extension over unreliable client content-type.
    _ = content_type

    stored_name = f"{uuid.uuid4().hex}{extension}"
    storage = get_storage()
    storage.save(stored_name, data)

    document = Document(
        title=meta.title,
        description=meta.description,
        original_filename=_safe_original_name(filename),
        stored_filename=stored_name,
        file_type=file_type,
        file_size=len(data),
        category=meta.category.value,
        uploaded_by=uploader.id,
        processing_status=ProcessingStatus.PENDING.value,
        processing_error=None,
    )
    db.add(document)
    commit_or_conflict(db, "Document could not be created.")
    db.refresh(document)

    process_document(db, document.id)
    return get_document_read(db, document.id)


def process_document(db: Session, document_id: int) -> Document:
    document = get_document(db, document_id)
    document.processing_status = ProcessingStatus.PROCESSING.value
    document.processing_error = None
    commit_or_conflict(db, "Document status could not be updated.")

    storage = get_storage()
    try:
        path = storage.open(document.stored_filename)
        extraction = document_extractor.extract_document(path, document.file_type)
        chunks = document_chunker.chunk_extraction(extraction)
        if not chunks:
            raise ExtractionError("No searchable text chunks were produced.")

        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        for chunk in chunks:
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                )
            )
        document.processing_status = ProcessingStatus.COMPLETED.value
        document.processing_error = None
        commit_or_conflict(db, "Document chunks could not be saved.")
    except ExtractionError as exc:
        document.processing_status = ProcessingStatus.FAILED.value
        document.processing_error = "Document processing failed. Check the file format and contents."
        logger.info("Document extraction failed for document_id=%s: %s", document_id, exc.detail)
        commit_or_conflict(db, "Document failure status could not be saved.")
    except Exception:  # noqa: BLE001
        document.processing_status = ProcessingStatus.FAILED.value
        document.processing_error = "Document processing failed due to an internal error."
        logger.exception("Unexpected document processing failure for document_id=%s", document_id)
        commit_or_conflict(db, "Document failure status could not be saved.")
    return get_document(db, document_id)


def delete_document(db: Session, actor: Student, document_id: int) -> None:
    require_admin(actor)
    document = get_document(db, document_id)
    stored = document.stored_filename
    db.delete(document)
    commit_or_conflict(db, "Document could not be deleted.")
    try:
        get_storage().delete(stored)
    except Exception:  # noqa: BLE001 - DB delete already succeeded
        pass


def open_document_file(db: Session, document_id: int) -> tuple[Document, Path]:
    document = get_document(db, document_id)
    path = get_storage().open(document.stored_filename)
    return document, path


def require_admin(student: Student) -> None:
    if student.role != UserRole.ADMIN.value:
        raise ForbiddenError("Admin privileges are required for this action.")


def serialize_document(document: Document, *, chunk_count: int = 0) -> DocumentRead:
    return DocumentRead(
        id=document.id,
        title=document.title,
        description=document.description,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size=document.file_size,
        category=document.category,
        uploaded_by=document.uploaded_by,
        processing_status=document.processing_status,
        processing_error=document.processing_error,
        chunk_count=chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _chunk_counts(db: Session, document_ids: list[int]) -> dict[int, int]:
    if not document_ids:
        return {}
    statement = (
        select(DocumentChunk.document_id, func.count())
        .where(DocumentChunk.document_id.in_(document_ids))
        .group_by(DocumentChunk.document_id)
    )
    return {document_id: count for document_id, count in db.execute(statement).all()}


def _validate_filename(filename: str) -> tuple[str, str]:
    name = Path(filename or "").name
    extension = Path(name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise BadRequestError(f"Unsupported file type. Allowed: {allowed}")
    return extension, ALLOWED_EXTENSIONS[extension]


def _safe_original_name(filename: str) -> str:
    name = Path(filename or "document").name.strip() or "document"
    return name[:255]
