from datetime import date


def _create_course(client, headers, code="DS201"):
    response = client.post(
        "/api/courses",
        headers=headers,
        json={"code": code, "title": "Data Structures", "credits": 4},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _enroll(client, headers, course_id):
    response = client.post(
        "/api/enrollments",
        headers=headers,
        json={"course_id": course_id, "semester": "Current"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_attendance_crud_and_isolation(client, auth_headers):
    headers_a, _ = auth_headers("a")
    headers_b, _ = auth_headers("b")
    course = _create_course(client, headers_a)
    _enroll(client, headers_a, course["id"])

    created = client.post(
        "/api/attendance",
        headers=headers_a,
        json={
            "course_id": course["id"],
            "attendance_date": "2026-02-01",
            "status": "present",
        },
    )
    assert created.status_code == 201, created.text
    record_id = created.json()["id"]

    client.post(
        "/api/attendance",
        headers=headers_a,
        json={
            "course_id": course["id"],
            "attendance_date": "2026-02-02",
            "status": "absent",
        },
    )

    overview = client.get("/api/attendance/overview", headers=headers_a)
    assert overview.status_code == 200
    body = overview.json()
    assert body["total_classes"] == 2
    assert body["attended_classes"] == 1
    assert body["missed_classes"] == 1
    assert body["attendance_percentage"] == 50.0

    foreign = client.get(f"/api/attendance/{record_id}", headers=headers_b)
    assert foreign.status_code == 404

    updated = client.patch(
        f"/api/attendance/{record_id}",
        headers=headers_a,
        json={"status": "late"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "late"

    deleted = client.delete(f"/api/attendance/{record_id}", headers=headers_a)
    assert deleted.status_code == 204


def test_attendance_requires_enrollment(client, auth_headers):
    headers, _ = auth_headers("c")
    course = _create_course(client, headers, code="CO202")
    response = client.post(
        "/api/attendance",
        headers=headers,
        json={
            "course_id": course["id"],
            "attendance_date": str(date.today()),
            "status": "present",
        },
    )
    assert response.status_code == 409


def test_academic_summary_and_isolation(client, auth_headers):
    headers_a, _ = auth_headers("d")
    headers_b, _ = auth_headers("e")
    course = _create_course(client, headers_a, code="DS301")
    _enroll(client, headers_a, course["id"])

    marks = [
        ("CAT1", 36, 50),
        ("CAT2", 42, 50),
        ("INTERNAL", 27, 30),
        ("FAT", 84, 100),
        ("LAB", 18, 20),
    ]
    for assessment_type, obtained, maximum in marks:
        response = client.post(
            "/api/marks",
            headers=headers_a,
            json={
                "course_id": course["id"],
                "assessment_type": assessment_type,
                "marks_obtained": obtained,
                "maximum_marks": maximum,
            },
        )
        assert response.status_code == 201, response.text

    summary = client.get("/api/academic/summary", headers=headers_a)
    assert summary.status_code == 200, summary.text
    payload = summary.json()
    assert payload["completed_courses"] == 1
    assert payload["gpa"]["status"] == "complete"
    assert payload["gpa"]["value"] == 9.0
    assert payload["cgpa"]["value"] == 9.0
    assert payload["courses"][0]["grade"] == "A"
    assert payload["courses"][0]["final_score"] == 84.0

    other = client.get("/api/academic/summary", headers=headers_b)
    assert other.status_code == 200
    assert other.json()["enrolled_courses"] == 0
    assert other.json()["gpa"]["value"] is None
