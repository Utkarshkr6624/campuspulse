def _course(client, headers, code="INT101", title="Intelligence Systems", credits=3):
    response = client.post(
        "/api/courses", headers=headers,
        json={"code": code, "title": title, "credits": credits},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _complete_marks(client, headers, course_id, cat1=35, cat2=45):
    marks = [
        ("CAT1", cat1, 50), ("CAT2", cat2, 50), ("INTERNAL", 27, 30),
        ("FAT", 90, 100), ("LAB", 18, 20),
    ]
    for assessment_type, obtained, maximum in marks:
        response = client.post("/api/marks", headers=headers, json={
            "course_id": course_id, "assessment_type": assessment_type,
            "marks_obtained": obtained, "maximum_marks": maximum,
        })
        assert response.status_code == 201, response.text


def test_intelligence_empty_single_semester_and_auth(client, auth_headers):
    assert client.get("/api/analytics/intelligence").status_code == 401
    headers, _ = auth_headers("int-empty")
    empty = client.get("/api/analytics/intelligence", headers=headers)
    assert empty.status_code == 200, empty.text
    assert empty.json()["data_status"] == "empty"
    assert empty.json()["semester_trend"] == []
    assert empty.json()["average_marks"] is None
    assert empty.json()["overall_attendance"] is None

    one = client.post("/api/semesters/setup", headers=headers, json={"current_semester": 1})
    assert one.status_code == 200
    course = _course(client, headers)
    enrollment = client.post("/api/enrollments", headers=headers, json={
        "course_id": course["id"], "semester": "Current",
    })
    assert enrollment.status_code == 201, enrollment.text
    client.post("/api/marks", headers=headers, json={
        "course_id": course["id"], "assessment_type": "CAT1",
        "marks_obtained": 36, "maximum_marks": 50,
    })
    body = client.get("/api/analytics/intelligence", headers=headers).json()
    assert body["data_status"] == "insufficient"
    assert "previous semester" in body["message"]
    assert body["ongoing_courses"] == 1
    assert body["courses"][0]["grade"] is None
    assert body["courses"][0]["cat1_to_cat2_change"] is None
    assert body["completed_credits"] == 0


def test_intelligence_semester_comparison_course_marks_attendance_and_isolation(client, auth_headers):
    headers, _ = auth_headers("int-main")
    foreign_headers, _ = auth_headers("int-foreign")
    setup = client.post("/api/semesters/setup", headers=headers, json={"current_semester": 2})
    assert setup.status_code == 200
    first, second = setup.json()
    course = _course(client, headers, code="INT201", title="Data Systems", credits=4)
    historic = client.post(f"/api/semesters/{first['id']}/courses", headers=headers, json={"courses": [{
        "course_id": course["id"], "course_name": "Data Systems", "course_code": "INT201",
        "credits": 4, "final_score": 72,
    }]})
    assert historic.status_code == 201, historic.text
    enrollment = client.post("/api/enrollments", headers=headers, json={
        "course_id": course["id"], "semester": "Current",
    })
    assert enrollment.status_code == 201, enrollment.text
    _complete_marks(client, headers, course["id"])
    for day, status in [("2026-03-10", "present"), ("2026-03-11", "present"), ("2026-03-12", "absent")]:
        response = client.post("/api/attendance", headers=headers, json={
            "course_id": course["id"], "attendance_date": day, "status": status,
        })
        assert response.status_code == 201, response.text

    response = client.get(
        f"/api/analytics/intelligence?first_semester_id={first['id']}&second_semester_id={second['id']}",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_status"] == "ready"
    assert body["current_sgpa"] == 9.0
    assert body["previous_sgpa"] == 8.0
    assert body["sgpa_change"] == 1.0
    assert body["best_semester_number"] == 2
    assert body["best_sgpa"] == 9.0
    assert body["lowest_semester_number"] == 1
    assert body["lowest_sgpa"] == 8.0
    assert body["completed_credits"] == 8
    assert body["current_semester_credits"] == 4
    assert body["average_marks"] == 79.5
    comparison = body["comparison"]
    assert comparison["sgpa_difference"] == 1.0
    assert comparison["average_marks_difference"] == 15.0
    assert comparison["credits_difference"] == 0
    assert comparison["attendance_difference"] is None
    current_course = next(item for item in body["courses"] if item["semester_number"] == 2)
    assert current_course["cat1_to_cat2_change"] == 20.0
    assert current_course["attendance_percentage"] == 66.67
    assert current_course["performance_category"] == "STRONG"
    assert any(item["type"] == "ASSESSMENT_TREND" for item in body["insights"])
    assert any(item["type"] == "ATTENDANCE_BELOW_THRESHOLD" for item in body["insights"])
    assert any(item["type"] == "COURSE_PERFORMANCE_TREND" for item in body["insights"])

    other = client.get(
        f"/api/analytics/intelligence?first_semester_id={first['id']}&second_semester_id={second['id']}",
        headers=foreign_headers,
    )
    assert other.status_code == 404


def test_intelligence_rejects_partial_comparison_selection(client, auth_headers):
    headers, _ = auth_headers("int-query")
    response = client.get("/api/analytics/intelligence?first_semester_id=1", headers=headers)
    assert response.status_code == 400
