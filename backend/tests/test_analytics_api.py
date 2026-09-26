from datetime import date, timedelta


def _create_course(client, headers, code="DS201", title="Data Structures", credits=4):
    response = client.post(
        "/api/courses",
        headers=headers,
        json={"code": code, "title": title, "credits": credits},
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


def _add_complete_marks(client, headers, course_id, scale=1.0):
    marks = [
        ("CAT1", 36 * scale, 50),
        ("CAT2", 42 * scale, 50),
        ("INTERNAL", 27 * scale, 30),
        ("FAT", 84 * scale, 100),
        ("LAB", 18 * scale, 20),
    ]
    for assessment_type, obtained, maximum in marks:
        response = client.post(
            "/api/marks",
            headers=headers,
            json={
                "course_id": course_id,
                "assessment_type": assessment_type,
                "marks_obtained": round(obtained, 2),
                "maximum_marks": maximum,
            },
        )
        assert response.status_code == 201, response.text


def test_analytics_requires_auth(client):
    assert client.get("/api/analytics/overview").status_code == 401
    assert client.get("/api/analytics/courses").status_code == 401
    assert client.get("/api/analytics/performance").status_code == 401
    assert client.get("/api/analytics/attendance").status_code == 401
    assert client.get("/api/analytics/insights").status_code == 401
    assert client.post("/api/analytics/gpa-simulation", json={"courses": []}).status_code == 401


def test_analytics_empty_and_insufficient_data(client, auth_headers):
    headers, _ = auth_headers("an1")
    overview = client.get("/api/analytics/overview", headers=headers)
    assert overview.status_code == 200
    body = overview.json()
    assert body["data_status"] == "empty"
    assert body["total_courses"] == 0
    assert body["grade_distribution"] == []

    performance = client.get("/api/analytics/performance", headers=headers)
    assert performance.status_code == 200
    assert performance.json()["status"] == "empty"

    course = _create_course(client, headers, code="AN101")
    _enroll(client, headers, course["id"])
    client.post(
        "/api/marks",
        headers=headers,
        json={
            "course_id": course["id"],
            "assessment_type": "CAT1",
            "marks_obtained": 40,
            "maximum_marks": 50,
        },
    )
    performance = client.get("/api/analytics/performance", headers=headers)
    assert performance.json()["status"] == "insufficient"
    assert len(performance.json()["points"]) == 1


def test_analytics_overview_courses_distribution_and_isolation(client, auth_headers):
    headers_a, _ = auth_headers("an2")
    headers_b, _ = auth_headers("an3")
    course = _create_course(client, headers_a, code="AN201")
    _enroll(client, headers_a, course["id"])
    _add_complete_marks(client, headers_a, course["id"])

    for day, status in [("2026-02-01", "present"), ("2026-02-02", "present"), ("2026-02-03", "absent")]:
        client.post(
            "/api/attendance",
            headers=headers_a,
            json={"course_id": course["id"], "attendance_date": day, "status": status},
        )

    overview = client.get("/api/analytics/overview", headers=headers_a)
    assert overview.status_code == 200
    body = overview.json()
    assert body["data_status"] == "ready"
    assert body["total_courses"] == 1
    assert body["completed_courses"] == 1
    assert body["completed_credits"] == 4
    assert body["gpa"]["value"] == 9.0
    assert body["cgpa"]["value"] == 9.0
    assert body["overall_attendance"] == 66.67
    assert any(bucket["letter"] == "A" and bucket["count"] == 1 for bucket in body["grade_distribution"])

    courses = client.get("/api/analytics/courses", headers=headers_a)
    assert courses.status_code == 200
    row = courses.json()[0]
    assert row["current_score"] == 84.0
    assert row["grade"] == "A"
    assert row["grade_point"] == 9.0
    assert row["completed_assessments"] == 5
    assert row["attendance_percentage"] == 66.67

    other = client.get("/api/analytics/overview", headers=headers_b)
    assert other.status_code == 200
    assert other.json()["total_courses"] == 0
    assert other.json()["gpa"]["value"] is None

    other_courses = client.get("/api/analytics/courses", headers=headers_b)
    assert other_courses.json() == []


def test_analytics_performance_trend(client, auth_headers):
    headers, _ = auth_headers("an4")
    course = _create_course(client, headers, code="AN301")
    _enroll(client, headers, course["id"])
    client.post(
        "/api/marks",
        headers=headers,
        json={
            "course_id": course["id"],
            "assessment_type": "CAT1",
            "marks_obtained": 36,
            "maximum_marks": 50,
            "assessment_date": "2026-01-10",
        },
    )
    client.post(
        "/api/marks",
        headers=headers,
        json={
            "course_id": course["id"],
            "assessment_type": "CAT2",
            "marks_obtained": 42,
            "maximum_marks": 50,
            "assessment_date": "2026-02-10",
        },
    )

    trend = client.get("/api/analytics/performance", headers=headers)
    assert trend.status_code == 200
    body = trend.json()
    assert body["status"] == "ready"
    assert len(body["points"]) == 2
    assert body["points"][0]["percentage"] == 72.0
    assert body["points"][1]["percentage"] == 84.0
    assert body["points"][1]["change_from_previous"] == 12.0


def test_analytics_attendance_health_and_insights(client, auth_headers):
    headers, _ = auth_headers("an5")
    course = _create_course(client, headers, code="AN401", title="AI Systems")
    _enroll(client, headers, course["id"])

    # 2 present / 1 absent => 66.67% => CRITICAL (< 75)
    for day, status in [("2026-03-01", "present"), ("2026-03-02", "present"), ("2026-03-03", "absent")]:
        client.post(
            "/api/attendance",
            headers=headers,
            json={"course_id": course["id"], "attendance_date": day, "status": status},
        )

    client.post(
        "/api/marks",
        headers=headers,
        json={
            "course_id": course["id"],
            "assessment_type": "CAT1",
            "marks_obtained": 20,
            "maximum_marks": 50,
        },
    )

    future = (date.today() + timedelta(days=5)).isoformat()
    client.post(
        "/api/exams",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "CAT 2",
            "exam_type": "CAT2",
            "exam_date": future,
        },
    )
    past = (date.today() - timedelta(days=2)).isoformat()
    client.post(
        "/api/assignments",
        headers=headers,
        json={
            "course_id": course["id"],
            "title": "Lab writeup",
            "due_date": past,
            "status": "TODO",
            "priority": "HIGH",
        },
    )

    attendance = client.get("/api/analytics/attendance", headers=headers)
    assert attendance.status_code == 200
    att = attendance.json()
    assert att["overall_health"] == "CRITICAL"
    assert "66.67%" in att["overall_message"]
    assert att["courses"][0]["health"] == "CRITICAL"

    insights = client.get("/api/analytics/insights", headers=headers)
    assert insights.status_code == 200
    types = {item["type"] for item in insights.json()["insights"]}
    assert "LOW_ATTENDANCE" in types
    assert "MISSING_ASSESSMENT" in types
    assert "UPCOMING_EXAM" in types
    assert "OVERDUE_ASSIGNMENT" in types


def test_gpa_simulation_does_not_mutate_data(client, auth_headers):
    headers, _ = auth_headers("an6")
    complete = _create_course(client, headers, code="AN501", title="Completed Course")
    incomplete = _create_course(client, headers, code="AN502", title="Incomplete Course", credits=3)
    _enroll(client, headers, complete["id"])
    _enroll(client, headers, incomplete["id"])
    _add_complete_marks(client, headers, complete["id"])
    client.post(
        "/api/marks",
        headers=headers,
        json={
            "course_id": incomplete["id"],
            "assessment_type": "CAT1",
            "marks_obtained": 40,
            "maximum_marks": 50,
        },
    )

    before = client.get("/api/academic/summary", headers=headers).json()
    assert before["gpa"]["value"] == 9.0
    marks_before = client.get("/api/marks", headers=headers).json()

    simulation = client.post(
        "/api/analytics/gpa-simulation",
        headers=headers,
        json={"courses": [{"course_id": incomplete["id"], "letter_grade": "S"}]},
    )
    assert simulation.status_code == 200, simulation.text
    body = simulation.json()
    assert body["label"] == "Projected / Hypothetical"
    assert body["current_gpa"]["value"] == 9.0
    assert body["projected_gpa"]["status"] == "complete"
    assert body["projected_gpa"]["value"] is not None
    assert body["projected_gpa"]["value"] > body["current_gpa"]["value"]

    after = client.get("/api/academic/summary", headers=headers).json()
    assert after["gpa"]["value"] == before["gpa"]["value"]
    assert after["completed_courses"] == before["completed_courses"]
    marks_after = client.get("/api/marks", headers=headers).json()
    assert marks_after == marks_before

    foreign_headers, _ = auth_headers("an7")
    foreign = client.get("/api/analytics/insights", headers=foreign_headers)
    assert foreign.status_code == 200
    assert foreign.json()["insights"] == [] or foreign.json()["status"] in {"empty", "ready"}
    # Isolation: foreign student must not see an6's course codes in insights
    for insight in foreign.json()["insights"]:
        assert insight.get("course_code") not in {"AN501", "AN502"}
