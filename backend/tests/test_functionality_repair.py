from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.db import session as db_session
from app.core.config import Settings
from app.models.student import Student


def test_auth_finds_legacy_email_case_and_whitespace_without_replacing_account(client):
    registered = client.post("/api/auth/register", json={
        "full_name": "Legacy Email",
        "email": "legacy.email@example.edu",
        "university_id": "LEGACYEMAIL",
        "password": "correct-horse",
    })
    assert registered.status_code == 201, registered.text
    assert registered.json()["student"]["email"] == "legacy.email@example.edu"
    original_student_id = registered.json()["student"]["id"]

    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    course = client.post("/api/courses", headers=headers, json={
        "code": "LEG101", "title": "Legacy Data", "credits": 3,
    })
    assert course.status_code == 201, course.text

    with db_session.SessionLocal() as db:
        student = db.get(Student, original_student_id)
        assert student is not None
        student.email = "Legacy.Email@Example.edu"
        db.commit()

    login = client.post("/api/auth/login", json={
        "email": "  LEGACY.email@EXAMPLE.edu  ",
        "password": "correct-horse",
    })
    assert login.status_code == 200, login.text
    assert login.json()["student"]["id"] == original_student_id
    logged_in_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    persisted_courses = client.get("/api/courses", headers=logged_in_headers)
    assert persisted_courses.status_code == 200
    assert [item["code"] for item in persisted_courses.json()] == ["LEG101"]

    wrong_password = client.post("/api/auth/login", json={
        "email": "legacy.email@example.edu",
        "password": "wrong-password",
    })
    assert wrong_password.status_code == 401

    duplicate = client.post("/api/auth/register", json={
        "full_name": "Duplicate",
        "email": " LEGACY.EMAIL@example.edu ",
        "university_id": "LEGACYEMAIL2",
        "password": "correct-horse",
    })
    assert duplicate.status_code == 409
    assert "log in instead" in duplicate.json()["detail"].lower()


def test_normalized_email_unique_index_rejects_direct_case_and_space_variant(client, auth_headers):
    _headers, student = auth_headers("normalized-index")
    with db_session.SessionLocal() as db:
        db.add(Student(
            full_name="Duplicate Email",
            email=f"  {student['email'].upper()}  ",
            university_id="DUP-NORMALIZED-EMAIL",
            password_hash="not-a-real-hash",
        ))
        with pytest.raises(IntegrityError):
            db.commit()


def test_database_url_falls_back_to_sqlite_when_not_configured(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(
        _env_file=None,
        jwt_secret_key="sqlite-fallback-test-secret-with-sufficient-length",
    )
    assert settings.database_url == "sqlite:///./campuspulse.db"


def test_student_academic_workflow_persists_and_is_private(client, auth_headers):
    headers_a, _ = auth_headers("flow-a")
    headers_b, _ = auth_headers("flow-b")

    duplicate_account = client.post("/api/auth/register", json={
        "full_name": "Duplicate Account",
        "email": "STUDENTFLOW-A@EXAMPLE.EDU",
        "university_id": "FLOW-A-DUPLICATE",
        "password": "correct-horse",
    })
    assert duplicate_account.status_code == 409
    assert client.post("/api/auth/login", json={
        "email": "studentflow-a@example.edu", "password": "wrong-password",
    }).status_code == 401

    semesters = client.post("/api/semesters/setup", headers=headers_a, json={"current_semester": 3})
    assert semesters.status_code == 200, semesters.text
    semester_one, semester_two, semester_three = semesters.json()
    for semester, year, sgpa, credits in [
        (semester_one, "2024–25", 8.57, 22),
        (semester_two, "2025–26", 8.62, 24),
    ]:
        updated = client.patch(
            f"/api/semesters/{semester['id']}",
            headers=headers_a,
            json={"academic_year": year, "recorded_sgpa": sgpa, "recorded_credits": credits},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["gpa"]["value"] == sgpa

    profile = client.patch(
        "/api/auth/academic-profile", headers=headers_a, json={"official_cgpa": 8.6}
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["official_cgpa"] == 8.6

    created = client.post("/api/courses", headers=headers_a, json={
        "code": "CSE2002", "title": "Data Structures and Algorithms", "credits": 4,
        "semester_id": semester_three["id"],
    })
    assert created.status_code == 201, created.text
    course = created.json()
    assert course["owner_id"] == profile.json()["id"]
    assert client.get("/api/enrollments", headers=headers_a).json()[0]["semester_id"] == semester_three["id"]

    expected_marks = [
        ("CAT1", 36, 50),
        ("CAT2", 44, 50),
        ("INTERNAL", 27, 30),
        ("FAT", 82, 100),
        ("LAB", 18, 20),
        ("MID SEMESTER EXAMINATION", 42, 50),
    ]
    created_marks = []
    for assessment_type, obtained, maximum in expected_marks:
        response = client.post("/api/marks", headers=headers_a, json={
            "course_id": course["id"], "assessment_type": assessment_type,
            "marks_obtained": obtained, "maximum_marks": maximum,
        })
        assert response.status_code == 201, response.text
        created_marks.append(response.json())

    duplicate = client.post("/api/marks", headers=headers_a, json={
        "course_id": course["id"], "assessment_type": "MID SEMESTER EXAMINATION",
        "marks_obtained": 40, "maximum_marks": 50,
    })
    assert duplicate.status_code == 409

    # Refresh-equivalent reads show persisted custom and standard assessments plus calculated results.
    marks = client.get("/api/marks", headers=headers_a)
    assert marks.status_code == 200
    assert len(marks.json()) == 6
    performance = client.get("/api/academic/courses", headers=headers_a).json()[0]
    assert performance["final_score"] == 83.8
    assert performance["grade"] == "A"
    assert all(item["assessment_type"] != "MID SEMESTER EXAMINATION" for item in performance["assessments"])
    summary = client.get("/api/academic/summary", headers=headers_a).json()
    assert summary["cgpa"]["value"] == 8.63
    assert summary["cgpa"]["value"] != profile.json()["official_cgpa"]

    # A second account cannot enumerate or use the first student's private course or marks.
    assert all(item["id"] != course["id"] for item in client.get("/api/courses", headers=headers_b).json())
    assert client.get(f"/api/courses/{course['id']}", headers=headers_b).status_code == 404
    assert client.get("/api/marks", headers=headers_b).json() == []
    foreign_enrollment = client.post("/api/enrollments", headers=headers_b, json={"course_id": course["id"]})
    assert foreign_enrollment.status_code == 404
    assert client.patch(
        f"/api/semesters/{semester_three['id']}", headers=headers_b,
        json={"academic_year": "2027–28"},
    ).status_code == 404
    assert client.delete(f"/api/semesters/{semester_three['id']}", headers=headers_b).status_code == 404
    assert client.patch(
        f"/api/marks/{created_marks[0]['id']}", headers=headers_b,
        json={"marks_obtained": 1},
    ).status_code == 404
    assert client.delete(f"/api/marks/{created_marks[0]['id']}", headers=headers_b).status_code == 404

    # Logout revokes the bearer token. A fresh login restores access to the same persisted data.
    old_token = headers_a["Authorization"]
    assert client.post("/api/auth/logout", headers=headers_a).status_code == 204
    assert client.get("/api/auth/me", headers={"Authorization": old_token}).status_code == 401
    login = client.post("/api/auth/login", json={"email": "studentflow-a@example.edu", "password": "correct-horse"})
    assert login.status_code == 200, login.text
    headers_after_login = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert len(client.get("/api/marks", headers=headers_after_login).json()) == 6
    assert len(client.get("/api/courses", headers=headers_after_login).json()) == 1

    edited = client.patch(f"/api/marks/{created_marks[0]['id']}", headers=headers_after_login, json={"marks_obtained": 40})
    assert edited.status_code == 200 and edited.json()["marks_obtained"] == 40
    deleted = client.delete(f"/api/marks/{created_marks[-1]['id']}", headers=headers_after_login)
    assert deleted.status_code == 204
    assert client.get("/api/marks", headers=headers_after_login).json()[-1]["assessment_type"] != "MID SEMESTER EXAMINATION"


def test_course_student_scope_and_admin_students_boundary(client, auth_headers, admin_headers):
    headers, _ = auth_headers("student-boundary")
    other_headers, _ = auth_headers("student-boundary-other")
    admin, _ = admin_headers("students-admin")
    assert client.get("/api/students", headers=headers).status_code == 403
    assert client.get("/api/students", headers=admin).status_code == 200

    semesters = client.post("/api/semesters/setup", headers=headers, json={"current_semester": 1})
    created = client.post("/api/courses", headers=headers, json={
        "code": "SAME101", "title": "Private Course", "credits": 3,
        "semester_id": semesters.json()[0]["id"],
    })
    assert created.status_code == 201
    foreign = client.post("/api/courses", headers=other_headers, json={
        "code": "SAME101", "title": "Other Private Course", "credits": 3,
    })
    assert foreign.status_code == 201, foreign.text
    assert foreign.json()["id"] != created.json()["id"]
    assert client.patch(
        f"/api/courses/{created.json()['id']}", headers=other_headers,
        json={"title": "Attempted takeover"},
    ).status_code == 404
    updated = client.patch(
        f"/api/courses/{created.json()['id']}", headers=headers,
        json={"title": "My Updated Course"},
    )
    assert updated.status_code == 200 and updated.json()["title"] == "My Updated Course"
    assert client.delete(f"/api/courses/{created.json()['id']}", headers=other_headers).status_code == 404
    assert client.delete(f"/api/courses/{created.json()['id']}", headers=headers).status_code == 204


def test_invalid_password_is_not_echoed(client):
    password = "🔒" * 25
    response = client.post("/api/auth/register", json={
        "full_name": "No Password Echo",
        "email": "no-echo@example.edu",
        "university_id": "NO-ECHO",
        "password": password,
    })
    assert response.status_code == 422
    assert password not in response.text


def test_security_headers_and_duplicate_exam_assignment_requests(client, auth_headers):
    headers, _ = auth_headers("integrity")
    health = client.get("/api/health")
    assert health.headers["x-content-type-options"] == "nosniff"
    assert health.headers["x-frame-options"] == "DENY"
    assert health.headers["referrer-policy"] == "strict-origin-when-cross-origin"

    semesters = client.post("/api/semesters/setup", headers=headers, json={"current_semester": 1})
    course = client.post("/api/courses", headers=headers, json={
        "code": "DUP101", "title": "Duplicate Guards", "credits": 3,
        "semester_id": semesters.json()[0]["id"],
    }).json()
    exam = {
        "course_id": course["id"], "title": "Midterm", "exam_type": "FAT",
        "exam_date": (date.today() + timedelta(days=20)).isoformat(),
    }
    assert client.post("/api/exams", headers=headers, json=exam).status_code == 201
    assert client.post("/api/exams", headers=headers, json=exam).status_code == 409
    assignment = {
        "course_id": course["id"], "title": "Lab report",
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
    }
    assert client.post("/api/assignments", headers=headers, json=assignment).status_code == 201
    assert client.post("/api/assignments", headers=headers, json=assignment).status_code == 409


def test_academic_records_survive_backend_restart(tmp_path: Path, monkeypatch):
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    from app import main as main_module
    from app.db import schema
    from app.db import session as db_session

    database_url = f"sqlite:///{(tmp_path / 'restart.db').as_posix()}"

    def connect_engine():
        restarted_engine = create_engine(database_url, connect_args={"check_same_thread": False})

        @event.listens_for(restarted_engine, "connect")
        def enable_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        monkeypatch.setattr(db_session, "engine", restarted_engine)
        monkeypatch.setattr(db_session, "SessionLocal", sessionmaker(bind=restarted_engine, autoflush=False, autocommit=False))
        monkeypatch.setattr(schema, "engine", restarted_engine)
        monkeypatch.setattr(schema, "SessionLocal", sessionmaker(bind=restarted_engine, autoflush=False, autocommit=False))
        return restarted_engine

    first_engine = connect_engine()
    with TestClient(main_module.app) as first_client:
        registered = first_client.post("/api/auth/register", json={
            "full_name": "Restart Test", "email": "restart@example.edu",
            "university_id": "RESTART1", "password": "correct-horse",
        })
        assert registered.status_code == 201, registered.text
        first_headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
        semester = first_client.post("/api/semesters/setup", headers=first_headers, json={"current_semester": 1}).json()[0]
        course = first_client.post("/api/courses", headers=first_headers, json={
            "code": "RST101", "title": "Restart Persistence", "credits": 3,
            "semester_id": semester["id"],
        })
        assert course.status_code == 201, course.text
        mark = first_client.post("/api/marks", headers=first_headers, json={
            "course_id": course.json()["id"], "assessment_type": "CUSTOM MIDTERM",
            "marks_obtained": 42, "maximum_marks": 50,
        })
        assert mark.status_code == 201, mark.text
        attendance = first_client.post("/api/attendance", headers=first_headers, json={
            "course_id": course.json()["id"], "attendance_date": date.today().isoformat(), "status": "present",
        })
        assert attendance.status_code == 201, attendance.text
        exam = first_client.post("/api/exams", headers=first_headers, json={
            "course_id": course.json()["id"], "title": "Restart exam", "exam_type": "FAT",
            "exam_date": (date.today() + timedelta(days=2)).isoformat(),
        })
        assert exam.status_code == 201, exam.text
        assignment = first_client.post("/api/assignments", headers=first_headers, json={
            "course_id": course.json()["id"], "title": "Restart assignment",
            "due_date": (date.today() + timedelta(days=4)).isoformat(),
        })
        assert assignment.status_code == 201, assignment.text
        assert first_client.post("/api/auth/logout", headers=first_headers).status_code == 204
    first_engine.dispose()

    second_engine = connect_engine()
    with TestClient(main_module.app) as second_client:
        login = second_client.post("/api/auth/login", json={
            "email": "restart@example.edu", "password": "correct-horse",
        })
        assert login.status_code == 200, login.text
        second_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert len(second_client.get("/api/semesters", headers=second_headers).json()) == 1
        assert second_client.get("/api/courses", headers=second_headers).json()[0]["code"] == "RST101"
        assert second_client.get("/api/marks", headers=second_headers).json()[0]["assessment_type"] == "CUSTOM MIDTERM"
        assert len(second_client.get("/api/attendance", headers=second_headers).json()) == 1
        assert second_client.get("/api/exams", headers=second_headers).json()[0]["title"] == "Restart exam"
        assert second_client.get("/api/assignments", headers=second_headers).json()[0]["title"] == "Restart assignment"
    second_engine.dispose()


def test_current_semester_creation_is_atomic_when_enrollment_attach_fails(client, auth_headers, monkeypatch):
    from app.core.exceptions import BadRequestError
    from app.services import semester_service

    headers, _ = auth_headers("semester-atomic")
    initial = client.post("/api/semesters/setup", headers=headers, json={"current_semester": 1})
    assert initial.status_code == 200
    course = client.post("/api/courses", headers=headers, json={
        "code": "ATOMIC1", "title": "Unassigned Course", "credits": 3,
    })
    assert course.status_code == 201

    def fail_attach(*_args, **_kwargs):
        raise BadRequestError("Simulated enrollment attach failure.")

    monkeypatch.setattr(semester_service, "_attach_unassigned_enrollments", fail_attach)
    response = client.post("/api/semesters", headers=headers, json={"number": 2, "set_current": True})
    assert response.status_code == 400
    semesters = client.get("/api/semesters", headers=headers).json()
    assert [item["number"] for item in semesters] == [1]
    assert semesters[0]["is_current"] is True


def test_historical_course_batch_rolls_back_on_duplicate_and_update_keeps_record_id(client, auth_headers):
    headers, _ = auth_headers("history-atomic")
    setup = client.post("/api/semesters/setup", headers=headers, json={"current_semester": 2})
    assert setup.status_code == 200
    previous = setup.json()[0]
    duplicate = {
        "course_name": "Historical Algorithms", "course_code": "HIST201",
        "credits": 3, "final_score": 82,
    }
    response = client.post(
        f"/api/semesters/{previous['id']}/courses", headers=headers,
        json={"courses": [duplicate, duplicate]},
    )
    assert response.status_code == 409
    assert client.get(f"/api/semesters/{previous['id']}", headers=headers).json()["historical_courses"] == []

    created = client.post(
        f"/api/semesters/{previous['id']}/courses", headers=headers,
        json={"courses": [duplicate]},
    )
    assert created.status_code == 201, created.text
    record_id = created.json()[0]["id"]
    edited = client.patch(
        f"/api/semesters/{previous['id']}/courses/{record_id}", headers=headers,
        json={**duplicate, "final_score": 88},
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["id"] == record_id
    assert edited.json()["final_score"] == 88
    assert len(client.get(f"/api/semesters/{previous['id']}", headers=headers).json()["historical_courses"]) == 1


def test_startup_refuses_incompatible_database_without_dropping_existing_rows(tmp_path: Path, monkeypatch):
    from app.db import schema

    database = tmp_path / "incompatible.db"
    legacy_engine = create_engine(f"sqlite:///{database.as_posix()}")
    with legacy_engine.begin() as connection:
        connection.execute(text("CREATE TABLE students (id INTEGER PRIMARY KEY, legacy_note TEXT)"))
        connection.execute(text("INSERT INTO students (id, legacy_note) VALUES (77, 'keep')"))
    monkeypatch.setattr(schema, "engine", legacy_engine)

    with pytest.raises(RuntimeError, match="Startup stopped without changing the database"):
        schema.prepare_database()

    with legacy_engine.connect() as connection:
        assert connection.execute(text("SELECT id, legacy_note FROM students")).one() == (77, "keep")
    legacy_engine.dispose()


def test_sqlite_foreign_keys_and_existing_data_integrity(client, auth_headers):
    from app.db import session as db_session

    headers, student = auth_headers("fk-integrity")
    setup = client.post("/api/semesters/setup", headers=headers, json={"current_semester": 1})
    course = client.post("/api/courses", headers=headers, json={
        "code": "FK101", "title": "Foreign Keys", "credits": 3,
        "semester_id": setup.json()[0]["id"],
    })
    assert course.status_code == 201
    with db_session.engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        assert connection.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
        connection.commit()
        with pytest.raises(IntegrityError):
            with connection.begin():
                connection.execute(text(
                    "INSERT INTO enrollments "
                    "(student_id, course_id, status, semester, created_at, updated_at) "
                    "VALUES (99999, 99999, 'enrolled', 'Semester 1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ))
        with pytest.raises(IntegrityError):
            with connection.begin():
                connection.execute(text(
                    "INSERT INTO course_marks "
                    "(student_id, course_id, assessment_type, marks_obtained, maximum_marks, created_at, updated_at) "
                    "VALUES (:student_id, :course_id, 'INVALID', 8, 7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ), {"student_id": student["id"], "course_id": course.json()["id"]})
