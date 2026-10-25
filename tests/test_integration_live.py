"""Comprehensive Integration Tests for Students Database CRUD Application.

Validates the full workflow using FastAPI TestClient with an isolated test database:
1. Frontend delivery (Dashboard HTML, CSS, JavaScript)
2. Backend & SQLite health check (/health)
3. Reading records via GET /students with pagination headers
4. Creating records via POST /students
5. Searching by name (?search=...)
6. Filtering by course (?course=...)
7. Retrieving individual student profile (GET /students/{id})
8. Full update via PUT /students/{id}
9. Partial update via PATCH /students/{id}
10. Deleting student record (DELETE /students/{id} -> 204)
11. Verifying deleted record returns 404 Not Found
12. Graceful error handling (409 Conflict for duplicate email, 422 for invalid inputs)
13. Isolation: Never modifies the production/application database (students.db).
"""

import pytest
from fastapi.testclient import TestClient


def test_frontend_delivery(client: TestClient):
    """Verify frontend static and dashboard endpoints deliver successfully."""
    # 1. Dashboard HTML
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    assert "Students Database Administration" in res_dash.text
    assert "studentsTableBody" in res_dash.text
    assert "healthStatusBadge" in res_dash.text

    # 2. CSS styles
    res_css = client.get("/static/css/style.css")
    assert res_css.status_code == 200
    assert "--primary-700" in res_css.text

    # 3. JavaScript frontend client
    res_js = client.get("/static/js/app.js")
    assert res_js.status_code == 200
    assert "loadStudents" in res_js.text


def test_backend_health(client: TestClient):
    """Verify backend API health check and database connectivity."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_full_crud_workflow_isolated(client: TestClient):
    """Verify full CRUD lifecycle and database operations against an isolated test database."""
    # 1. Read initial state
    res_list = client.get("/students")
    assert res_list.status_code == 200
    assert res_list.headers.get("X-Total-Count") == "0"
    assert res_list.json() == []

    # 2. Create student 1
    payload_1 = {
        "name": "Eleanor Vance",
        "email": "eleanor.vance@example.edu",
        "date_of_birth": "2001-04-12",
        "course": "Computer Science",
        "phone": "+1 555-0199",
        "address": "104 Campus Drive, Suite 302",
        "enrollment_date": "2024-09-01",
    }
    res_create_1 = client.post("/students", json=payload_1)
    assert res_create_1.status_code == 201
    s1 = res_create_1.json()
    s1_id = s1["id"]
    assert s1["name"] == "Eleanor Vance"
    assert s1["email"] == "eleanor.vance@example.edu"

    # 3. Create student 2
    payload_2 = {
        "name": "Julian Croft",
        "email": "julian.croft@example.edu",
        "date_of_birth": "2000-11-22",
        "course": "Data Science",
        "phone": "+1 555-0188",
        "enrollment_date": "2024-09-01",
    }
    res_create_2 = client.post("/students", json=payload_2)
    assert res_create_2.status_code == 201
    s2 = res_create_2.json()
    s2_id = s2["id"]
    assert s2["name"] == "Julian Croft"

    # 4. List students and verify total count
    res_all = client.get("/students")
    assert res_all.status_code == 200
    assert res_all.headers.get("X-Total-Count") == "2"
    assert len(res_all.json()) == 2

    # 5. Search by student name
    res_search = client.get("/students?search=Eleanor")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert len(search_data) == 1
    assert search_data[0]["id"] == s1_id

    # 6. Filter by course
    res_filter = client.get("/students?course=Data Science")
    assert res_filter.status_code == 200
    filter_data = res_filter.json()
    assert len(filter_data) == 1
    assert filter_data[0]["id"] == s2_id

    # 7. Retrieve student profile by ID
    res_profile = client.get(f"/students/{s1_id}")
    assert res_profile.status_code == 200
    assert res_profile.json()["email"] == "eleanor.vance@example.edu"

    # 8. Update using PUT
    payload_1_update = payload_1.copy()
    payload_1_update["phone"] = "+1 555-9900"
    payload_1_update["course"] = "Artificial Intelligence"
    res_put = client.put(f"/students/{s1_id}", json=payload_1_update)
    assert res_put.status_code == 200
    assert res_put.json()["phone"] == "+1 555-9900"
    assert res_put.json()["course"] == "Artificial Intelligence"

    # 9. Update using PATCH
    res_patch = client.patch(f"/students/{s2_id}", json={"phone": "+1 555-8888"})
    assert res_patch.status_code == 200
    assert res_patch.json()["phone"] == "+1 555-8888"

    # 10. Delete student 2
    res_delete = client.delete(f"/students/{s2_id}")
    assert res_delete.status_code == 204

    # 11. Verify student 2 returns 404 after deletion
    res_check_del = client.get(f"/students/{s2_id}")
    assert res_check_del.status_code == 404

    # 12. Error handling: Duplicate email conflict (409)
    res_dup = client.post("/students", json=payload_1)
    assert res_dup.status_code == 409
    assert "already exists" in res_dup.json()["detail"]

    # 13. Error handling: Invalid birth date (422)
    invalid_dob = payload_1.copy()
    invalid_dob["email"] = "unique.email@example.edu"
    invalid_dob["date_of_birth"] = "2099-01-01"
    res_inv = client.post("/students", json=invalid_dob)
    assert res_inv.status_code == 422
