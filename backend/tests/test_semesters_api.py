def _setup(client, headers, current=3):
    response = client.post("/api/semesters/setup", headers=headers, json={"current_semester": current})
    assert response.status_code == 200, response.text
    return response.json()


def test_semester_setup_history_gpa_and_account_isolation(client, auth_headers):
    headers_a, _ = auth_headers("semester-a")
    headers_b, _ = auth_headers("semester-b")

    assert client.get("/api/semesters", headers=headers_a).json() == []
    semesters = _setup(client, headers_a, 3)
    assert [item["number"] for item in semesters] == [1, 2, 3]
    assert [item["status"] for item in semesters] == ["PREVIOUS", "PREVIOUS", "CURRENT"]

    semester_one = semesters[0]["id"]
    added = client.post(
        f"/api/semesters/{semester_one}/courses",
        headers=headers_a,
        json={"courses": [
            {"course_name": "Mathematics", "course_code": "MA101", "credits": 4, "grade": "A"},
            {"course_name": "Programming", "course_code": "CS101", "credits": 3, "grade": "S"},
        ]},
    )
    assert added.status_code == 201, added.text
    assert [item["grade_point"] for item in added.json()] == [9.0, 10.0]

    details = client.get(f"/api/semesters/{semester_one}", headers=headers_a)
    assert details.status_code == 200
    assert details.json()["gpa"]["value"] == round((4 * 9 + 3 * 10) / 7, 2)
    assert details.json()["total_credits"] == 7

    cgpa = client.get("/api/academic/cgpa", headers=headers_a)
    assert cgpa.status_code == 200
    assert cgpa.json()["value"] == details.json()["gpa"]["value"]
    assert client.get(f"/api/semesters/{semester_one}", headers=headers_b).status_code == 404

    duplicate = client.post("/api/semesters", headers=headers_a, json={"number": 1})
    assert duplicate.status_code == 409


def test_current_semester_uses_existing_enrollment_and_marks(client, auth_headers):
    headers, _ = auth_headers("semester-current")
    current = _setup(client, headers, 2)[1]
    course_response = client.post(
        "/api/courses", headers=headers,
        json={"code": "SEM201", "title": "Current Course", "credits": 3},
    )
    course_id = course_response.json()["id"]
    enrollment = client.post(
        "/api/enrollments", headers=headers,
        json={"course_id": course_id, "semester": "Current"},
    )
    assert enrollment.status_code == 201, enrollment.text
    assert enrollment.json()["semester_id"] == current["id"]

    for assessment, obtained, maximum in [
        ("CAT1", 45, 50), ("CAT2", 45, 50), ("INTERNAL", 27, 30),
        ("FAT", 90, 100), ("LAB", 18, 20),
    ]:
        response = client.post(
            "/api/marks", headers=headers,
            json={"course_id": course_id, "assessment_type": assessment,
                  "marks_obtained": obtained, "maximum_marks": maximum},
        )
        assert response.status_code == 201, response.text

    detail = client.get(f"/api/semesters/{current['id']}", headers=headers).json()
    assert len(detail["enrolled_courses"]) == 1
    assert detail["enrolled_courses"][0]["grade"] == "S"
    assert detail["gpa"]["value"] == 10.0
