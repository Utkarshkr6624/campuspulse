import os
from pathlib import Path

os.environ["JWT_SECRET_KEY"] = "phase4-test-secret-key-with-enough-length-123456"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

_TEST_STORAGE = Path(__file__).resolve().parent / "_test_storage"
_TEST_STORAGE.mkdir(exist_ok=True)
os.environ["DOCUMENT_STORAGE_PATH"] = str(_TEST_STORAGE)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.roles import UserRole
from app.db import session as db_session
from app.db.session import Base
from app.main import app
from app.models.student import Student
from app.services import grading_scheme_service
from app.storage import get_storage

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
db_session.engine = engine
db_session.SessionLocal = TestingSessionLocal


@pytest.fixture()
def client():
    get_storage.cache_clear()
    for path in _TEST_STORAGE.glob("*"):
        if path.is_file():
            path.unlink()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        grading_scheme_service.ensure_default_scheme(db)
    finally:
        db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    get_storage.cache_clear()


@pytest.fixture()
def auth_headers(client: TestClient):
    def _register(suffix: str = "a"):
        response = client.post(
            "/api/auth/register",
            json={
                "full_name": f"Test Student {suffix}",
                "email": f"student{suffix}@example.edu",
                "university_id": f"TS{suffix.upper()}",
                "password": "correct-horse",
            },
        )
        assert response.status_code == 201, response.text
        token = response.json()["access_token"]
        student = response.json()["student"]
        return {"Authorization": f"Bearer {token}"}, student

    return _register


@pytest.fixture()
def admin_headers(auth_headers):
    def _admin(suffix: str = "adm"):
        headers, student = auth_headers(suffix)
        db = TestingSessionLocal()
        try:
            row = db.get(Student, student["id"])
            assert row is not None
            row.role = UserRole.ADMIN.value
            db.commit()
            student["role"] = UserRole.ADMIN.value
        finally:
            db.close()
        return headers, student

    return _admin
