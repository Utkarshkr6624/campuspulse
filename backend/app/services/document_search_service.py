"""Keyword document search — designed to be replaceable with semantic search later."""

from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentSearchHit, DocumentSearchResponse
from app.core.document_enums import ProcessingStatus

_TOKEN_RE = re.compile(r"[a-z0-9]{2,}", re.IGNORECASE)


def search_documents(db: Session, query: str, *, limit: int = 20) -> DocumentSearchResponse:
    cleaned = " ".join(query.split()).strip()
    tokens = _tokenize(cleaned)
    if not cleaned or not tokens:
        return DocumentSearchResponse(query=cleaned, total=0, results=[])

    # Broad candidate fetch: any token in title/description/chunk content.
    filters = []
    for token in tokens:
        like = f"%{token}%"
        filters.append(Document.title.ilike(like))
        filters.append(Document.description.ilike(like))
        filters.append(DocumentChunk.content.ilike(like))

    statement = (
        select(DocumentChunk)
        .join(Document)
        .where(
            Document.processing_status == ProcessingStatus.COMPLETED.value,
            or_(*filters),
        )
        .options(joinedload(DocumentChunk.document))
        .limit(500)
    )
    chunks = list(db.scalars(statement).unique().all())

    # Also include title-only matches that may have no chunk hit if somehow empty —
    # completed docs always have chunks, so ranking below is enough.

    scored: list[DocumentSearchHit] = []
    for chunk in chunks:
        document = chunk.document
        score, matched_in = _score(document, chunk, tokens)
        if score <= 0:
            continue
        scored.append(
            DocumentSearchHit(
                document_id=document.id,
                title=document.title,
                category=document.category,
                file_type=document.file_type,
                page_number=chunk.page_number,
                snippet=_snippet(chunk.content, tokens),
                score=round(score, 3),
                matched_in=matched_in,
            )
        )

    # Deduplicate by document keeping best chunk hit, then keep secondary hits if useful.
    best_by_doc: dict[int, DocumentSearchHit] = {}
    extras: list[DocumentSearchHit] = []
    for hit in sorted(scored, key=lambda item: item.score, reverse=True):
        current = best_by_doc.get(hit.document_id)
        if current is None:
            best_by_doc[hit.document_id] = hit
        elif len(extras) < limit:
            # Keep alternate snippets with distinct pages.
            if hit.page_number != current.page_number or hit.snippet != current.snippet:
                extras.append(hit)

    ranked = sorted(best_by_doc.values(), key=lambda item: item.score, reverse=True)
    combined = ranked + extras
    combined.sort(key=lambda item: item.score, reverse=True)
    results = combined[:limit]
    return DocumentSearchResponse(query=cleaned, total=len(results), results=results)


def _tokenize(query: str) -> list[str]:
    seen: set[str] = set()
    tokens: list[str] = []
    for match in _TOKEN_RE.findall(query.lower()):
        if match not in seen:
            seen.add(match)
            tokens.append(match)
    return tokens


def _score(document: Document, chunk: DocumentChunk, tokens: list[str]) -> tuple[float, str]:
    title = (document.title or "").lower()
    description = (document.description or "").lower()
    content = (chunk.content or "").lower()
    score = 0.0
    matched_in = "content"
    for token in tokens:
        if token in title:
            score += 3.0
            matched_in = "title"
        if token in description:
            score += 1.5
            if matched_in == "content":
                matched_in = "description"
        occurrences = content.count(token)
        if occurrences:
            score += min(2.0, 0.6 * occurrences)
    return score, matched_in


def _snippet(content: str, tokens: list[str], *, radius: int = 90) -> str:
    lower = content.lower()
    positions = []
    for token in tokens:
        index = lower.find(token)
        if index >= 0:
            positions.append(index)
    if not positions:
        text = content.strip()
        return text[: radius * 2] + ("…" if len(text) > radius * 2 else "")

    center = min(positions)
    start = max(0, center - radius)
    end = min(len(content), center + radius)
    snippet = content[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(content):
        snippet = snippet + "…"
    return snippet
