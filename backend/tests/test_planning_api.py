def _course(client, headers):
    created = client.post("/api/courses", headers=headers, json={
        "code": "PL101", "title": "Planning", "credits": 3,
    })
    assert created.status_code == 201, created.text
    enrolled = client.post("/api/enrollments", headers=headers, json={
        "course_id": created.json()["id"], "semester": "Current",
    })
    assert enrolled.status_code == 201, enrolled.text
    return created.json()["id"]


def test_targets_scenarios_are_owned_and_scenario_marks_are_hypothetical(client, auth_headers):
    headers_a, _ = auth_headers("plan-a")
    headers_b, _ = auth_headers("plan-b")
    course_id = _course(client, headers_a)
    mark = client.post("/api/marks", headers=headers_a, json={
        "course_id": course_id, "assessment_type": "CAT1",
        "marks_obtained": 30, "maximum_marks": 50,
    })
    assert mark.status_code == 201, mark.text
    for assessment_type, obtained, maximum in [
        ("CAT2", 40, 50), ("INTERNAL", 24, 30), ("FAT", 80, 100), ("LAB", 16, 20),
    ]:
        response = client.post("/api/marks", headers=headers_a, json={
            "course_id": course_id, "assessment_type": assessment_type,
            "marks_obtained": obtained, "maximum_marks": maximum,
        })
        assert response.status_code == 201, response.text

    target = client.put("/api/targets/SGPA", headers=headers_a, json={"target_value": 8.5})
    assert target.status_code == 200
    assert target.json()["status"] == "IN_PROGRESS"
    assert client.get("/api/targets", headers=headers_b).json() == []

    scenario_data = {
        "title": "Better CAT1",
        "assessments": [{
            "course_id": course_id, "assessment_type": "CAT1",
            "marks_obtained": 45, "maximum_marks": 50,
        }],
    }
    created = client.post("/api/scenarios", headers=headers_a, json=scenario_data)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["projection"]["courses"][0]["projected_score"] > body["projection"]["courses"][0]["current_score"]
    assert client.get("/api/scenarios/" + str(body["id"]), headers=headers_b).status_code == 404
    assert client.patch("/api/scenarios/" + str(body["id"]), headers=headers_b, json={"title": "stolen"}).status_code == 404
    assert client.delete("/api/scenarios/" + str(body["id"]), headers=headers_b).status_code == 404

    actual = client.get("/api/marks/courses/" + str(course_id), headers=headers_a).json()
    cat1 = next(item for item in actual if item["assessment_type"] == "CAT1")
    assert cat1["marks_obtained"] == 30
    empty_target = client.put("/api/targets/SGPA", headers=headers_b, json={"target_value": 7.0})
    assert empty_target.status_code == 200
    assert empty_target.json()["status"] == "INSUFFICIENT_DATA"
    assert client.delete("/api/targets/SGPA", headers=headers_b).status_code == 204
    assert len(client.get("/api/targets", headers=headers_a).json()) == 1


def test_scenario_validation_and_compare(client, auth_headers):
    headers, _ = auth_headers("plan-validation")
    course_id = _course(client, headers)
    invalid = client.post("/api/scenarios/preview", headers=headers, json={"assessments": [{
        "course_id": course_id, "assessment_type": "FINAL",
        "marks_obtained": 110, "maximum_marks": 100,
    }]})
    assert invalid.status_code == 422
    entries = []
    for title in ("Option A", "Option B"):
        response = client.post("/api/scenarios", headers=headers, json={
            "title": title,
            "assessments": [{
                "course_id": course_id, "assessment_type": "CAT1",
                "marks_obtained": 35, "maximum_marks": 50,
            }],
        })
        assert response.status_code == 201, response.text
        entries.append(response.json()["id"])
    compared = client.post("/api/scenarios/compare", headers=headers, json={"scenario_ids": entries})
    assert compared.status_code == 200
    assert len(compared.json()["scenarios"]) == 2
