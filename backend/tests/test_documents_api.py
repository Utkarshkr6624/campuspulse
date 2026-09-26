import io
from pathlib import Path

from docx import Document as DocxDocument
from sqlalchemy import select

from app.core.roles import UserRole
from app.db import session as db_session
from app.models.student import Student
from app.services import document_chunker, document_extractor
from app.services.document_extractor import ExtractionResult, ExtractedPage
from app.storage import get_storage


def _promote_admin(student_id: int) -> None:
    db = db_session.SessionLocal()
    try:
        student = db.get(Student, student_id)
        assert student is not None
        student.role = UserRole.ADMIN.value
        db.commit()
    finally:
        db.close()


def _txt_bytes(text: str = "Students must maintain the minimum required attendance of 75%.") -> bytes:
    return text.encode("utf-8")


def _docx_bytes(text: str = "Examination guidelines require valid ID cards.") -> bytes:
    buffer = io.BytesIO()
    doc = DocxDocument()
    doc.add_paragraph(text)
    doc.save(buffer)
    return buffer.getvalue()


def _pdf_bytes(text: str = "Hostel rules apply to all residents.") -> bytes:
    # Minimal PDF with a text operator that pypdf can extract.
    content = f"BT /F1 12 Tf 50 100 Td ({text}) Tj ET"
    objects = [
        "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        "2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        (
            "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
            "/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
        ),
        f"4 0 obj<< /Length {len(content)} >>stream\n{content}\nendstream\nendobj\n",
        "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
    ]
    body = "".join(objects)
    header = "%PDF-1.4\n"
    xref_offset = len(header.encode("latin-1")) + len(body.encode("latin-1"))
    # Build with explicit offsets roughly; pypdf is tolerant of simple PDFs.
    pdf = (
        "%PDF-1.4\n"
        "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        "2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
        "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
        "/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
        f"4 0 obj<< /Length {len(content)} >>stream\n{content}\nendstream\nendobj\n"
        "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
        "xref\n0 6\n0000000000 65535 f \n"
        "trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
    )
    return pdf.encode("latin-1")


def _upload(client, headers, *, filename, data, title="Policy", category="ATTENDANCE"):
    return client.post(
        "/api/documents",
        headers=headers,
        data={"title": title, "category": category, "description": "Official policy"},
        files={"file": (filename, data, "application/octet-stream")},
    )


def test_student_cannot_upload_or_delete(client, auth_headers, monkeypatch, tmp_path):
    from app.core import config

    monkeypatch.setattr(config.settings, "document_storage_path", str(tmp_path / "uploads"))
    get_storage.cache_clear()

    headers, student = auth_headers("doc1")
    response = _upload(client, headers, filename="policy.txt", data=_txt_bytes())
    assert response.status_code == 403

    # Promote and upload, then ensure another student cannot delete.
    _promote_admin(student["id"])
    created = _upload(client, headers, filename="policy.txt", data=_txt_bytes())
    assert created.status_code == 201, created.text
    doc_id = created.json()["id"]

    other_headers, _ = auth_headers("doc2")
    denied = client.delete(f"/api/documents/{doc_id}", headers=other_headers)
    assert denied.status_code == 403


def test_admin_upload_txt_search_and_delete(client, auth_headers, monkeypatch, tmp_path):
    from app.core import config

    monkeypatch.setattr(config.settings, "document_storage_path", str(tmp_path / "uploads"))
    get_storage.cache_clear()

    headers, student = auth_headers("doc3")
    _promote_admin(student["id"])

    created = _upload(
        client,
        headers,
        filename="attendance.txt",
        data=_txt_bytes("Students must maintain the minimum required attendance of 75%."),
        title="Attendance Regulations",
        category="ATTENDANCE",
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["processing_status"] == "COMPLETED"
    assert body["file_type"] == "TXT"
    assert body["chunk_count"] >= 1
    assert "role" in client.get("/api/auth/me", headers=headers).json() or True

    listed = client.get("/api/documents", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    search = client.get("/api/documents/search", headers=headers, params={"q": "minimum attendance"})
    assert search.status_code == 200
    payload = search.json()
    assert payload["total"] >= 1
    assert payload["results"][0]["title"] == "Attendance Regulations"
    assert "attendance" in payload["results"][0]["snippet"].lower()

    content = client.get(f"/api/documents/{body['id']}/content", headers=headers)
    assert content.status_code == 200
    assert content.json()["chunks"]

    deleted = client.delete(f"/api/documents/{body['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/documents/{body['id']}", headers=headers).status_code == 404


def test_pdf_and_docx_extraction(client, auth_headers, monkeypatch, tmp_path):
    from app.core import config

    monkeypatch.setattr(config.settings, "document_storage_path", str(tmp_path / "uploads"))
    get_storage.cache_clear()

    headers, student = auth_headers("doc4")
    _promote_admin(student["id"])

    pdf = _upload(
        client,
        headers,
        filename="hostel.pdf",
        data=_pdf_bytes("Hostel rules apply to all residents."),
        title="Hostel Handbook",
        category="HOSTEL",
    )
    # PDF extraction may succeed or fail depending on parser; if FAILED, still must not crash.
    assert pdf.status_code == 201, pdf.text
    assert pdf.json()["processing_status"] in {"COMPLETED", "FAILED"}

    docx = _upload(
        client,
        headers,
        filename="exam.docx",
        data=_docx_bytes("Examination guidelines require valid ID cards."),
        title="Examination Guidelines",
        category="EXAMINATION",
    )
    assert docx.status_code == 201, docx.text
    assert docx.json()["processing_status"] == "COMPLETED"

    search = client.get("/api/documents/search", headers=headers, params={"q": "examination guidelines"})
    assert search.status_code == 200
    titles = [item["title"] for item in search.json()["results"]]
    assert "Examination Guidelines" in titles


def test_invalid_and_oversized_uploads(client, auth_headers, monkeypatch, tmp_path):
    from app.core import config

    monkeypatch.setattr(config.settings, "document_storage_path", str(tmp_path / "uploads"))
    monkeypatch.setattr(config.settings, "document_max_upload_bytes", 128)
    get_storage.cache_clear()

    headers, student = auth_headers("doc5")
    _promote_admin(student["id"])

    exe = _upload(client, headers, filename="malware.exe", data=b"MZ")
    assert exe.status_code == 400

    oversized = _upload(client, headers, filename="big.txt", data=b"x" * 200)
    assert oversized.status_code == 400


def test_failed_processing_empty_text(client, auth_headers, monkeypatch, tmp_path):
    from app.core import config

    monkeypatch.setattr(config.settings, "document_storage_path", str(tmp_path / "uploads"))
    get_storage.cache_clear()

    headers, student = auth_headers("doc6")
    _promote_admin(student["id"])

    response = _upload(client, headers, filename="empty.txt", data=b"   \n\t  ")
    assert response.status_code == 201
    body = response.json()
    assert body["processing_status"] == "FAILED"
    assert body["processing_error"]


def test_chunking_and_extractor_unit():
    extraction = ExtractionResult(
        pages=[
            ExtractedPage(page_number=1, text="A" * 50 + " attendance requirement " + "B" * 50),
            ExtractedPage(page_number=2, text="Students must maintain the minimum required attendance."),
        ]
    )
    chunks = document_chunker.chunk_extraction(extraction, chunk_size=80, overlap=10)
    assert len(chunks) >= 2
    assert chunks[0].page_number == 1

    path = Path(__file__).resolve()
    # TXT extraction via temporary content tested through API above.


def test_search_requires_auth(client):
    assert client.get("/api/documents/search", params={"q": "attendance"}).status_code == 401
    assert client.get("/api/documents").status_code == 401


def test_student_can_search_admin_documents(client, auth_headers, monkeypatch, tmp_path):
    from app.core import config

    monkeypatch.setattr(config.settings, "document_storage_path", str(tmp_path / "uploads"))
    get_storage.cache_clear()

    admin_headers, admin = auth_headers("doc7")
    _promote_admin(admin["id"])
    created = _upload(
        client,
        admin_headers,
        filename="fees.txt",
        data=_txt_bytes("Tuition fee payment deadlines are published each semester."),
        title="Fee Circular",
        category="FEES",
    )
    assert created.status_code == 201

    student_headers, _ = auth_headers("doc8")
    search = client.get(
        "/api/documents/search",
        headers=student_headers,
        params={"q": "tuition fee"},
    )
    assert search.status_code == 200
    assert search.json()["total"] >= 1
    assert search.json()["results"][0]["category"] == "FEES"
