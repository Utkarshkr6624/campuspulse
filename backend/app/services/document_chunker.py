"""Split extracted document text into searchable chunks."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.document_extractor import ExtractedPage, ExtractionResult

DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 120


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    page_number: int | None


def chunk_extraction(
    extraction: ExtractionResult,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size.")

    chunks: list[TextChunk] = []
    index = 0
    for page in extraction.pages:
        for piece in _split_text(page.text, chunk_size=chunk_size, overlap=overlap):
            chunks.append(TextChunk(chunk_index=index, content=piece, page_number=page.page_number))
            index += 1
    return chunks


def _split_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    pieces: list[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            # Prefer breaking on whitespace near the end.
            break_at = cleaned.rfind(" ", start, end)
            if break_at > start + chunk_size // 2:
                end = break_at
        piece = cleaned[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return pieces
