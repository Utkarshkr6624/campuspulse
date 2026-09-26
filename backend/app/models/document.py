from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.document_enums import DOCUMENT_CATEGORY_VALUES, PROCESSING_STATUS_VALUES
from app.db.session import Base
from app.models.mixins import TimestampMixin

_category_values = ", ".join(f"'{value}'" for value in DOCUMENT_CATEGORY_VALUES)
_status_values = ", ".join(f"'{value}'" for value in PROCESSING_STATUS_VALUES)


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(f"category IN ({_category_values})", name="ck_document_category"),
        CheckConstraint(f"processing_status IN ({_status_values})", name="ck_document_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    file_type: Mapped[str] = mapped_column(String(16))
    file_size: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(32), index=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    processing_status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploader: Mapped["Student"] = relationship(back_populates="uploaded_documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")
