"""Document text extraction — separate from upload and search."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ExtractionError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int | None
    text: str


@dataclass(frozen=True)
class ExtractionResult:
    pages: list[ExtractedPage]

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text.strip())


def extract_document(path: Path, file_type: str) -> ExtractionResult:
    normalized = file_type.upper()
    if normalized == "PDF":
        return _extract_pdf(path)
    if normalized == "TXT":
        return _extract_txt(path)
    if normalized == "DOCX":
        return _extract_docx(path)
    raise ExtractionError(f"Unsupported file type for extraction: {file_type}")


def _extract_pdf(path: Path) -> ExtractionResult:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExtractionError("PDF extraction dependency is not installed.") from exc

    try:
        reader = PdfReader(str(path))
        pages: list[ExtractedPage] = []
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(ExtractedPage(page_number=index, text=text))
        if not pages:
            raise ExtractionError("PDF contained no extractable text.")
        return ExtractionResult(pages=pages)
    except ExtractionError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface as processing failure
        raise ExtractionError(f"PDF extraction failed: {exc}") from exc


def _extract_txt(path: Path) -> ExtractionResult:
    try:
        raw = path.read_bytes()
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ExtractionError("Could not decode text file.")
        cleaned = text.strip()
        if not cleaned:
            raise ExtractionError("Text file is empty.")
        return ExtractionResult(pages=[ExtractedPage(page_number=1, text=cleaned)])
    except ExtractionError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"Text extraction failed: {exc}") from exc


def _extract_docx(path: Path) -> ExtractionResult:
    try:
        from docx import Document as DocxDocument
    except ImportError as exc:
        raise ExtractionError("DOCX extraction dependency is not installed.") from exc

    try:
        document = DocxDocument(str(path))
        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        if not paragraphs:
            raise ExtractionError("DOCX contained no extractable text.")
        text = "\n".join(paragraphs)
        return ExtractionResult(pages=[ExtractedPage(page_number=1, text=text)])
    except ExtractionError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"DOCX extraction failed: {exc}") from exc
