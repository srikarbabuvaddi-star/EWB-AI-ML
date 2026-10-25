"""Automated test suite for Students Database CRUD Application.

Covers all 11 required test areas:
1. Application health check
2. Create student
3. List students (search, filter, pagination)
4. Retrieve student by ID
5. Update using PUT
6. Update using PATCH
7. Delete student
8. Student not found
9. Duplicate email rejection
10. Invalid input rejection
11. Database persistence
"""

from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Student
from app.database import Base


# --------------------------------------------------------------------------
# 1. Application Health Check & Welcome Tests
# --------------------------------------------------------------------------
def test_health_check(client: TestClient):
    """Test 1: Verify the /health endpoint returns HTTP 200 and database is connected."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_welcome_endpoint(client: TestClient):
    """Verify root GET / returns an introductory welcome response with links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["docs_url"] == "/docs"
    assert data["dashboard_url"] == "/dashboard"


# --------------------------------------------------------------------------
# 2. Create Student Tests
# --------------------------------------------------------------------------
def test_create_student_success(client: TestClient, sample_student_data: dict):
    """Test 2: Verify POST /students creates a student and returns HTTP 201."""
    response = client.post("/students", json=sample_student_data)
    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["name"] == sample_student_data["name"]
    assert data["email"] == sample_student_data["email"].lower()
    assert data["date_of_birth"] == sample_student_data["date_of_birth"]
    assert data["course"] == sample_student_data["course"]
    assert data["phone"] == sample_student_data["phone"]
    assert data["address"] == sample_student_data["address"]
    assert data["enrollment_date"] == sample_student_data["enrollment_date"]
    assert "created_at" in data
    assert "updated_at" in data


# --------------------------------------------------------------------------
# 3. List Students (Search, Filter, Pagination) Tests
# --------------------------------------------------------------------------
def test_list_students_with_search_filter_pagination(
    client: TestClient,
    sample_student_data: dict,
    sample_student_data_2: dict,
):
    """Test 3: Verify GET /students supports listing, name search, course filtering, and pagination."""
    # 1. Create two students
    res1 = client.post("/students", json=sample_student_data)
    assert res1.status_code == 201
    res2 = client.post("/students", json=sample_student_data_2)
    assert res2.status_code == 201

    # 2. List all students (default pagination)
    list_res = client.get("/students")
    assert list_res.status_code == 200
    all_students = list_res.json()
    assert len(all_students) == 2
    assert list_res.headers.get("X-Total-Count") == "2"

    # 3. Search by name (case-insensitive substring)
    search_res = client.get("/students?search=jane")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data) == 1
    assert search_data[0]["name"] == "Jane Doe"

    # 4. Filter by course
    filter_res = client.get("/students?course=Data Science")
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    assert len(filter_data) == 1
    assert filter_data[0]["name"] == "John Smith"
    assert filter_data[0]["course"] == "Data Science"

    # 5. Pagination: limit=1, offset=0
    page1 = client.get("/students?limit=1&offset=0")
    assert page1.status_code == 200
    assert len(page1.json()) == 1
    assert page1.headers.get("X-Total-Count") == "2"

    # 6. Pagination: limit=1, offset=1
    page2 = client.get("/students?limit=1&offset=1")
    assert page2.status_code == 200
    assert len(page2.json()) == 1
    assert page2.json()[0]["id"] != page1.json()[0]["id"]


# --------------------------------------------------------------------------
# 4. Retrieve Student by ID Tests
# --------------------------------------------------------------------------
def test_retrieve_student_by_id(client: TestClient, sample_student_data: dict):
    """Test 4: Verify GET /students/{id} retrieves an individual student profile."""
    create_res = client.post("/students", json=sample_student_data)
    student_id = create_res.json()["id"]

    get_res = client.get(f"/students/{student_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == student_id
    assert data["name"] == sample_student_data["name"]
    assert data["email"] == sample_student_data["email"].lower()


# --------------------------------------------------------------------------
# 5. Update Using PUT Tests
# --------------------------------------------------------------------------
def test_update_student_put(client: TestClient, sample_student_data: dict):
    """Test 5: Verify PUT /students/{id} replaces editable details with validated data."""
    create_res = client.post("/students", json=sample_student_data)
    student_id = create_res.json()["id"]

    replacement_data = {
        "name": "Jane Watson",
        "date_of_birth": "2001-05-15",
        "email": "jane.watson@example.edu",
        "phone": "+1 555-9999",
        "course": "Artificial Intelligence",
        "address": "999 Innovation Way",
        "enrollment_date": "2024-10-01",
    }

    put_res = client.put(f"/students/{student_id}", json=replacement_data)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["id"] == student_id
    assert updated["name"] == "Jane Watson"
    assert updated["email"] == "jane.watson@example.edu"
    assert updated["course"] == "Artificial Intelligence"
    assert updated["phone"] == "+1 555-9999"


# --------------------------------------------------------------------------
# 6. Update Using PATCH Tests
# --------------------------------------------------------------------------
def test_update_student_patch(client: TestClient, sample_student_data: dict):
    """Test 6: Verify PATCH /students/{id} updates only supplied fields."""
    create_res = client.post("/students", json=sample_student_data)
    student_id = create_res.json()["id"]

    # Partially update only the phone and course
    patch_payload = {
        "phone": "+1 555-7777",
        "course": "Robotics & Automation",
    }

    patch_res = client.patch(f"/students/{student_id}", json=patch_payload)
    assert patch_res.status_code == 200
    patched = patch_res.json()

    # Updated fields
    assert patched["phone"] == "+1 555-7777"
    assert patched["course"] == "Robotics & Automation"

    # Unchanged fields should remain intact
    assert patched["name"] == sample_student_data["name"]
    assert patched["email"] == sample_student_data["email"].lower()
    assert patched["date_of_birth"] == sample_student_data["date_of_birth"]


# --------------------------------------------------------------------------
# 7. Delete Student Tests
# --------------------------------------------------------------------------
def test_delete_student(client: TestClient, sample_student_data: dict):
    """Test 7: Verify DELETE /students/{id} removes student and returns HTTP 204."""
    create_res = client.post("/students", json=sample_student_data)
    student_id = create_res.json()["id"]

    # Delete student
    del_res = client.delete(f"/students/{student_id}")
    assert del_res.status_code == 204

    # Subsequent GET should return 404
    get_res = client.get(f"/students/{student_id}")
    assert get_res.status_code == 404


# --------------------------------------------------------------------------
# 8. Student Not Found Tests
# --------------------------------------------------------------------------
def test_student_not_found(client: TestClient, sample_student_data: dict):
    """Test 8: Verify operations on a non-existent student ID return HTTP 404."""
    non_existent_id = 99999

    # GET missing
    res_get = client.get(f"/students/{non_existent_id}")
    assert res_get.status_code == 404
    assert f"Student with ID {non_existent_id} was not found" in res_get.json()["detail"]

    # PUT missing
    res_put = client.put(f"/students/{non_existent_id}", json=sample_student_data)
    assert res_put.status_code == 404

    # PATCH missing
    res_patch = client.patch(f"/students/{non_existent_id}", json={"name": "New Name"})
    assert res_patch.status_code == 404

    # DELETE missing
    res_delete = client.delete(f"/students/{non_existent_id}")
    assert res_delete.status_code == 404


# --------------------------------------------------------------------------
# 9. Duplicate Email Rejection Tests
# --------------------------------------------------------------------------
def test_duplicate_email_rejection(
    client: TestClient,
    sample_student_data: dict,
    sample_student_data_2: dict,
):
    """Test 9: Verify duplicate email returns HTTP 409 Conflict during create and update."""
    # 1. Create first student
    res1 = client.post("/students", json=sample_student_data)
    assert res1.status_code == 201

    # 2. Attempt creating second student with identical email
    duplicate_payload = sample_student_data_2.copy()
    duplicate_payload["email"] = sample_student_data["email"].upper()  # Case-insensitive duplicate test
    res_dup = client.post("/students", json=duplicate_payload)
    assert res_dup.status_code == 409
    assert "already exists" in res_dup.json()["detail"]

    # 3. Create second student with distinct email
    res2 = client.post("/students", json=sample_student_data_2)
    assert res2.status_code == 201
    second_id = res2.json()["id"]

    # 4. Attempt updating second student's email to first student's email via PUT
    update_payload = sample_student_data_2.copy()
    update_payload["email"] = sample_student_data["email"]
    res_put_dup = client.put(f"/students/{second_id}", json=update_payload)
    assert res_put_dup.status_code == 409
    assert "already exists" in res_put_dup.json()["detail"]

    # 5. Attempt updating second student's email via PATCH
    res_patch_dup = client.patch(f"/students/{second_id}", json={"email": sample_student_data["email"]})
    assert res_patch_dup.status_code == 409
    assert "already exists" in res_patch_dup.json()["detail"]


# --------------------------------------------------------------------------
# 10. Invalid Input Rejection Tests
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "invalid_field,invalid_value,expected_error_substr",
    [
        ("name", "", "at least 2 characters"),
        ("name", "   ", "Student name cannot be empty"),
        ("name", "A", "at least 2 characters"),
        ("email", "not-a-valid-email", "valid email address"),
        ("email", "@missinguser.com", "valid email address"),
        ("date_of_birth", "2099-01-01", "cannot be in the future"),
        ("date_of_birth", "1890-05-10", "cannot be prior to the year 1900"),
        ("phone", "invalid-phone-abc!@#", "Phone number must contain"),
    ],
)
def test_invalid_input_rejection(
    client: TestClient,
    sample_student_data: dict,
    invalid_field: str,
    invalid_value: str,
    expected_error_substr: str,
):
    """Test 10: Verify invalid inputs are rejected with HTTP 422 Unprocessable Entity."""
    payload = sample_student_data.copy()
    payload[invalid_field] = invalid_value

    response = client.post("/students", json=payload)
    assert response.status_code == 422
    response_text = response.text.lower()
    assert invalid_field.lower() in response_text
    assert expected_error_substr.lower() in response_text


# --------------------------------------------------------------------------
# 11. Database Persistence Across Sessions Test
# --------------------------------------------------------------------------
def test_database_persistence(tmp_path):
    """Test 11: Verify student records persist across separate database connections and restarts."""
    # Create a real SQLite file in a temporary directory
    db_file = tmp_path / "persistence_test.db"
    db_url = f"sqlite:///{db_file}"

    file_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=file_engine)
    FileSession = sessionmaker(bind=file_engine, autocommit=False, autoflush=False)

    # Session 1: Insert record and commit
    session1: Session = FileSession()
    student = Student(
        name="Persistent Student",
        date_of_birth=date(1999, 8, 20),
        email="persistent@example.edu",
        phone="+1 555-0100",
        course="Cybersecurity",
    )
    session1.add(student)
    session1.commit()
    saved_id = student.id
    session1.close()

    # Dispose connection pool to simulate complete server shutdown/restart
    file_engine.dispose()

    # Session 2: Connect via brand new engine to the existing SQLite database file
    new_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    NewFileSession = sessionmaker(bind=new_engine, autocommit=False, autoflush=False)
    session2: Session = NewFileSession()

    persisted_student = session2.query(Student).filter(Student.id == saved_id).first()
    assert persisted_student is not None
    assert persisted_student.id == saved_id
    assert persisted_student.name == "Persistent Student"
    assert persisted_student.email == "persistent@example.edu"
    assert persisted_student.course == "Cybersecurity"

    session2.close()
    new_engine.dispose()
