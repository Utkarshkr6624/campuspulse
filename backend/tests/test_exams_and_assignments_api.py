from datetime import date, timedelta


def _create_course(client, headers, code="DS201", title="Data Structures"):
    response = client.post(
        "/api/courses",
        headers=headers,
        json={"code": code, "title": title, "credits": 4},
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


def _future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def _past(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def test_exam_crud_filtering_and_isolation(client, auth_headers):
    headers_a, _ = auth_headers("exa")
    headers_b, _ = auth_headers("exb")
    course = _create_course(client, headers_a)
    _enroll(client, headers_a, course["id"])

    created = client.post(
        "/api/exams",
        headers=headers_a,
        json={
            "course_id": course["id"],
            "title": "CAT 2",
            "exam_type": "CAT2",
            "exam_date": _future(10),
            "start_time": "10:00:00",
            "end_time": "12:00:00",
            "location": "Room AB-204",
            "description": "Units 3-5",
        },
    )
    assert created.status_code == 201, created.text
    exam = created.json()
    assert exam["exam_type"] == "CAT2"
    assert exam["is_upcoming"] is True
    assert exam["days_until"] == 10
    assert exam["course"]["code"] == "DS201"
    exam_id = exam["id"]

    client.post(
        "/api/exams",
        headers=headers_a,
        json={
            "course_id": course["id"],
            "title": "Past quiz",
            "exam_type": "QUIZ",
            "exam_date": _past(3),
        },
    )

    upcoming = client.get("/api/exams", headers=headers_a, params={"upcoming": True})
    assert upcoming.status_code == 200
    assert len(upcoming.json()) == 1
    assert upcoming.json()[0]["id"] == exam_id

    by_type = client.get("/api/exams", headers=headers_a, params={"exam_type": "CAT2"})
    assert len(by_type.json()) == 1

    by_range = client.get(
        "/api/exams",
        headers=headers_a,
        params={"date_from": _future(1), "date_to": _future(20)},
    )
    assert len(by_range.json()) == 1

    fetched = client.get(f"/api/exams/{exam_id}", headers=headers_a)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "CAT 2"

    foreign = client.get(f"/api/exams/{exam_id}", headers=headers_b)
    assert foreign.status_code == 404

    foreign_list = client.get("/api/exams", headers=headers_b)
    assert foreign_list.status_code == 200
    assert foreign_list.json() == []

    updated = client.patch(
        f"/api/exams/{exam_id}",
        headers=headers_a,
        json={"title": "CAT 2 Revised", "location": "Hall B"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "CAT 2 Revised"
    assert updated.json()["location"] == "Hall B"

    foreign_update = client.patch(
        f"/api/exams/{exam_id}",
        headers=headers_b,
        json={"title": "Hijack"},
    )
    assert foreign_update.status_code == 404

    deleted = client.delete(f"/api/exams/{exam_id}", headers=headers_a)
    assert deleted.status_code == 204
    assert client.get(f"/api/exams/{exam_id}", headers=headers_a).status_code == 404


def test_exam_requires_auth_enrollment_and_valid_input(client, auth_headers):
    headers, _ = auth_headers("exc")
    course = _create_course(client, headers, code="CO202", title="Computer Organization")

    unauthenticated = client.get("/api/exams")
    assert unauthenticated.status_code == 401

    without_enrollment = client.post(
        "/api/exams",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "FAT",
            "exam_type": "FAT",
            "exam_date": _future(20),
        },
    )
    assert without_enrollment.status_code == 409

    _enroll(client, headers, course["id"])

    invalid_type = client.post(
        "/api/exams",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Mystery",
            "exam_type": "MIDTERM",
            "exam_date": _future(5),
        },
    )
    assert invalid_type.status_code == 422

    invalid_times = client.post(
        "/api/exams",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Bad window",
            "exam_type": "LAB",
            "exam_date": _future(5),
            "start_time": "14:00:00",
            "end_time": "13:00:00",
        },
    )
    assert invalid_times.status_code == 422


def test_assignment_crud_filtering_and_isolation(client, auth_headers):
    headers_a, _ = auth_headers("asa")
    headers_b, _ = auth_headers("asb")
    course = _create_course(client, headers_a, code="DS301")
    _enroll(client, headers_a, course["id"])

    created = client.post(
        "/api/assignments",
        headers=headers_a,
        json={
            "course_id": course["id"],
            "title": "Lab report",
            "description": "Trees and graphs",
            "due_date": _future(5),
            "due_time": "23:59:00",
            "status": "TODO",
            "priority": "HIGH",
        },
    )
    assert created.status_code == 201, created.text
    assignment = created.json()
    assert assignment["priority"] == "HIGH"
    assert assignment["is_overdue"] is False
    assert assignment["is_due_today"] is False
    assert assignment["days_until"] == 5
    assignment_id = assignment["id"]

    overdue = client.post(
        "/api/assignments",
        headers=headers_a,
        json={
            "course_id": course["id"],
            "title": "Old homework",
            "due_date": _past(2),
            "status": "TODO",
            "priority": "MEDIUM",
        },
    )
    assert overdue.status_code == 201
    overdue_body = overdue.json()
    assert overdue_body["is_overdue"] is True
    assert overdue_body["days_until"] == -2

    completed = client.post(
        "/api/assignments",
        headers=headers_a,
        json={
            "course_id": course["id"],
            "title": "Finished quiz prep",
            "due_date": _past(1),
            "status": "COMPLETED",
            "priority": "LOW",
        },
    )
    assert completed.status_code == 201

    upcoming = client.get("/api/assignments", headers=headers_a, params={"upcoming": True})
    assert upcoming.status_code == 200
    assert len(upcoming.json()) == 1
    assert upcoming.json()[0]["id"] == assignment_id

    by_status = client.get("/api/assignments", headers=headers_a, params={"status": "COMPLETED"})
    assert len(by_status.json()) == 1

    by_priority = client.get("/api/assignments", headers=headers_a, params={"priority": "HIGH"})
    assert len(by_priority.json()) == 1

    open_only = client.get("/api/assignments", headers=headers_a, params={"completed": False})
    assert len(open_only.json()) == 2

    foreign = client.get(f"/api/assignments/{assignment_id}", headers=headers_b)
    assert foreign.status_code == 404

    foreign_list = client.get("/api/assignments", headers=headers_b)
    assert foreign_list.json() == []

    updated = client.patch(
        f"/api/assignments/{assignment_id}",
        headers=headers_a,
        json={"status": "IN_PROGRESS", "priority": "MEDIUM"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "IN_PROGRESS"
    assert updated.json()["priority"] == "MEDIUM"

    foreign_delete = client.delete(f"/api/assignments/{assignment_id}", headers=headers_b)
    assert foreign_delete.status_code == 404

    deleted = client.delete(f"/api/assignments/{assignment_id}", headers=headers_a)
    assert deleted.status_code == 204


def test_assignment_requires_auth_enrollment_and_valid_input(client, auth_headers):
    headers, _ = auth_headers("asc")
    course = _create_course(client, headers, code="AI401", title="AI Fundamentals")

    unauthenticated = client.post(
        "/api/assignments",
        json={
            "course_id": course["id"],
            "title": "Essay",
            "due_date": _future(3),
        },
    )
    assert unauthenticated.status_code == 401

    without_enrollment = client.post(
        "/api/assignments",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Essay",
            "due_date": _future(3),
        },
    )
    assert without_enrollment.status_code == 409

    _enroll(client, headers, course["id"])

    invalid_status = client.post(
        "/api/assignments",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Essay",
            "due_date": _future(3),
            "status": "DONE",
        },
    )
    assert invalid_status.status_code == 422

    invalid_priority = client.post(
        "/api/assignments",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Essay",
            "due_date": _future(3),
            "priority": "URGENT",
        },
    )
    assert invalid_priority.status_code == 422


def test_upcoming_event_ordering_via_list_apis(client, auth_headers):
    headers, _ = auth_headers("ord")
    course = _create_course(client, headers, code="PL500")
    _enroll(client, headers, course["id"])

    later_exam = client.post(
        "/api/exams",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Later exam",
            "exam_type": "FAT",
            "exam_date": _future(20),
        },
    )
    sooner_exam = client.post(
        "/api/exams",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Sooner exam",
            "exam_type": "CAT1",
            "exam_date": _future(4),
        },
    )
    assert later_exam.status_code == 201
    assert sooner_exam.status_code == 201

    exams = client.get("/api/exams", headers=headers, params={"upcoming": True}).json()
    assert [item["title"] for item in exams] == ["Sooner exam", "Later exam"]

    later_assignment = client.post(
        "/api/assignments",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Later due",
            "due_date": _future(12),
            "status": "TODO",
        },
    )
    sooner_assignment = client.post(
        "/api/assignments",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Sooner due",
            "due_date": _future(2),
            "status": "IN_PROGRESS",
        },
    )
    assert later_assignment.status_code == 201
    assert sooner_assignment.status_code == 201

    assignments = client.get("/api/assignments", headers=headers, params={"upcoming": True}).json()
    assert [item["title"] for item in assignments] == ["Sooner due", "Later due"]
