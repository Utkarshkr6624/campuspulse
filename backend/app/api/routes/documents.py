from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_student
from app.core.document_enums import DocumentCategory, ProcessingStatus
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.db.session import get_db
from app.models.student import Student
from app.schemas.document import (
    DocumentContentRead,
    DocumentCreateMeta,
    DocumentRead,
    DocumentSearchResponse,
)
from app.services import document_search_service, document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(
    category: DocumentCategory | None = Query(default=None),
    processing_status: ProcessingStatus | None = Query(default=None),
    _student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return document_service.list_documents(db, category=category, status=processing_status)


@router.get("/search", response_model=DocumentSearchResponse)
def search_documents(
    q: str = Query(min_length=1, max_length=200),
    _student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> DocumentSearchResponse:
    return document_search_service.search_documents(db, q)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: int,
    _student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> DocumentRead:
    return document_service.get_document_read(db, document_id)


@router.get("/{document_id}/content", response_model=DocumentContentRead)
def get_document_content(
    document_id: int,
    _student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> DocumentContentRead:
    return document_service.get_document_content(db, document_id)


@router.get("/{document_id}/file")
def download_document_file(
    document_id: int,
    _student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> FileResponse:
    document, path = document_service.open_document_file(db, document_id)
    media = {
        "PDF": "application/pdf",
        "TXT": "text/plain",
        "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(document.file_type, "application/octet-stream")
    return FileResponse(
        path,
        media_type=media,
        filename=document.original_filename,
        content_disposition_type="inline",
    )


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    category: DocumentCategory = Form(default=DocumentCategory.GENERAL),
    description: str | None = Form(default=None),
    file: UploadFile = File(...),
    admin: Student = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> DocumentRead:
    if file.filename is None:
        raise BadRequestError("A file is required.")
    try:
        data = await file.read(settings.document_max_upload_bytes + 1)
    finally:
        await file.close()
    if len(data) > settings.document_max_upload_bytes:
        raise BadRequestError(
            f"File exceeds the maximum size of {settings.document_max_upload_bytes} bytes."
        )
    meta = DocumentCreateMeta(title=title, description=description, category=category)
    return document_service.upload_document(
        db,
        admin,
        meta=meta,
        filename=file.filename,
        content_type=file.content_type,
        data=data,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    admin: Student = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> Response:
    document_service.delete_document(db, admin, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
