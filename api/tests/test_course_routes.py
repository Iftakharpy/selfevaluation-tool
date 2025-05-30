# FilePath: api/tests/test_course_routes.py
from fastapi.testclient import TestClient
from http import HTTPStatus # For status codes
import uuid # For generating unique data

# Base data for courses (can be templates)
course_template_1 = {
    "name": "Introduction to Programming",
    "code": "CS101",
    "description": "Fundamentals of programming."
}
course_template_2 = {
    "name": "Data Structures",
    "code": "CS201",
    "description": "Advanced data organization."
}

def create_unique_course_payload(base_payload: dict) -> dict:
    """Creates a new course payload with a unique code and potentially name."""
    unique_suffix = uuid.uuid4().hex[:6]
    payload = base_payload.copy()
    payload["code"] = f"{base_payload['code']}_{unique_suffix}"
    # Optionally, make name unique too if tests require distinct names beyond code
    # payload["name"] = f"{base_payload['name']} ({unique_suffix})"
    return payload

def test_create_course_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client # Unpack, we only need client here for action
    
    unique_course_payload = create_unique_course_payload(course_template_1)
    response = client.post("/api/v1/courses/", json=unique_course_payload)
    
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["name"] == unique_course_payload["name"]
    assert data["code"] == unique_course_payload["code"]
    assert "id" in data

def test_create_course_fail_as_student(authenticated_student_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_student_data_and_client
    
    unique_course_payload = create_unique_course_payload(course_template_1)
    response = client.post("/api/v1/courses/", json=unique_course_payload)
    
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "Teacher role required" in response.json()["detail"]

def test_create_course_fail_unauthenticated(client: TestClient):
    unique_course_payload = create_unique_course_payload(course_template_1)
    response = client.post("/api/v1/courses/", json=unique_course_payload)
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]

def test_create_course_duplicate_code(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    
    unique_course_payload = create_unique_course_payload(course_template_1)
    # Create first course
    response1 = client.post("/api/v1/courses/", json=unique_course_payload)
    assert response1.status_code == HTTPStatus.CREATED
    
    # Attempt to create again with the exact same (now existing) unique code
    response2 = client.post("/api/v1/courses/", json=unique_course_payload)
    assert response2.status_code == HTTPStatus.BAD_REQUEST
    assert "already exists" in response2.json()["detail"]

def test_list_courses_as_student(
    client: TestClient, 
    authenticated_student_data_and_client: tuple[TestClient, dict],
    authenticated_teacher_data_and_client: tuple[TestClient, dict]
):
    # Teacher logs in via authenticated_teacher_data_and_client
    # This sets the cookie on the shared `client` instance for the teacher.
    teacher_client, _ = authenticated_teacher_data_and_client
    
    # Create courses with unique codes specific to this test execution
    course1_payload = create_unique_course_payload(course_template_1)
    course2_payload = create_unique_course_payload(course_template_2)
    
    res1 = teacher_client.post("/api/v1/courses/", json=course1_payload)
    assert res1.status_code == HTTPStatus.CREATED, res1.text
    res2 = teacher_client.post("/api/v1/courses/", json=course2_payload)
    assert res2.status_code == HTTPStatus.CREATED, res2.text

    # Student logs in via authenticated_student_data_and_client
    # This re-sets the cookie on the shared `client` instance for the student.
    student_client, _ = authenticated_student_data_and_client

    response = student_client.get("/api/v1/courses/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)
    
    retrieved_codes = {item["code"] for item in data}
    assert course1_payload["code"] in retrieved_codes, f"Course {course1_payload['code']} not found in list"
    assert course2_payload["code"] in retrieved_codes, f"Course {course2_payload['code']} not found in list"
    # The length assertion is made less strict for parallel runs.
    # We're primarily checking if the courses *we* created are visible.
    assert len(data) >= 2


def test_list_courses_unauthenticated(client: TestClient):
    response = client.get("/api/v1/courses/")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]

def test_get_course_by_id_success(
    client: TestClient, # Base client
    authenticated_student_data_and_client: tuple[TestClient, dict],
    authenticated_teacher_data_and_client: tuple[TestClient, dict]
):
    teacher_client, _ = authenticated_teacher_data_and_client # Logs in teacher
    
    unique_course_payload = create_unique_course_payload(course_template_1)
    create_response = teacher_client.post("/api/v1/courses/", json=unique_course_payload)
    assert create_response.status_code == HTTPStatus.CREATED
    course_id = create_response.json()["id"]

    student_client, _ = authenticated_student_data_and_client # Logs in student
    response = student_client.get(f"/api/v1/courses/{course_id}")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == course_id
    assert data["name"] == unique_course_payload["name"]

def test_get_course_not_found(authenticated_student_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_student_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00" # A valid ObjectId format but unlikely to exist
    response = client.get(f"/api/v1/courses/{non_existent_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "Course not found" in response.json()["detail"]

def test_get_course_invalid_id_format(authenticated_student_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_student_data_and_client
    response = client.get("/api/v1/courses/invalid-objectid-format")
    assert response.status_code == HTTPStatus.BAD_REQUEST # Your router checks ObjectId.is_valid
    assert "Invalid course ID format" in response.json()["detail"]

def test_update_course_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    
    original_course_payload = create_unique_course_payload(course_template_1)
    create_response = client.post("/api/v1/courses/", json=original_course_payload)
    assert create_response.status_code == HTTPStatus.CREATED
    course_id = create_response.json()["id"]

    update_payload = {"name": "Updated Course Name", "description": "Updated description."}
    response = client.put(f"/api/v1/courses/{course_id}", json=update_payload)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["description"] == update_payload["description"]
    assert data["code"] == original_course_payload["code"] # Code was not updated

def test_update_course_fail_as_student(client: TestClient):
    # Setup: Teacher creates a course
    teacher_unique_suffix = uuid.uuid4().hex[:8]
    teacher_signup_data = {"username": f"t_update_{teacher_unique_suffix}@example.com", "display_name": "T Update", "role": "teacher", "password": "password"}
    client.post("/api/v1/users/signup", json=teacher_signup_data)
    login_response = client.post("/api/v1/users/login", json={"username": teacher_signup_data["username"], "password": "password"})
    assert login_response.status_code == HTTPStatus.OK
    
    course_payload = create_unique_course_payload(course_template_1)
    create_response = client.post("/api/v1/courses/", json=course_payload)
    assert create_response.status_code == HTTPStatus.CREATED
    course_id = create_response.json()["id"]

    # Action: Student attempts to update
    student_unique_suffix = uuid.uuid4().hex[:8]
    student_signup_data = {"username": f"s_update_{student_unique_suffix}@example.com", "display_name": "S Update", "role": "student", "password": "password"}
    client.post("/api/v1/users/signup", json=student_signup_data)
    login_response_student = client.post("/api/v1/users/login", json={"username": student_signup_data["username"], "password": "password"})
    assert login_response_student.status_code == HTTPStatus.OK

    update_payload = {"name": "Student Attempt Update"}
    response = client.put(f"/api/v1/courses/{course_id}", json=update_payload)
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "Teacher role required" in response.json()["detail"]

def test_update_course_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    update_payload = {"name": "Attempt Update Non Existent"}
    response = client.put(f"/api/v1/courses/{non_existent_id}", json=update_payload)
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_update_course_duplicate_code_on_update(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    
    course1_unique = create_unique_course_payload(course_template_1)
    course2_unique_base_payload = create_unique_course_payload(course_template_2) # Ensures course2 starts unique
    
    res1 = client.post("/api/v1/courses/", json=course1_unique)
    assert res1.status_code == HTTPStatus.CREATED
    
    create_res_2 = client.post("/api/v1/courses/", json=course2_unique_base_payload)
    assert create_res_2.status_code == HTTPStatus.CREATED
    course_2_id = create_res_2.json()["id"]

    # Try to update course 2's code to course 1's unique code
    update_payload = {"code": course1_unique["code"]}
    response = client.put(f"/api/v1/courses/{course_2_id}", json=update_payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "already exists" in response.json()["detail"]

def test_delete_course_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    
    unique_course_payload = create_unique_course_payload(course_template_1)
    create_response = client.post("/api/v1/courses/", json=unique_course_payload)
    assert create_response.status_code == HTTPStatus.CREATED
    course_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/courses/{course_id}")
    assert delete_response.status_code == HTTPStatus.NO_CONTENT

    get_response = client.get(f"/api/v1/courses/{course_id}")
    assert get_response.status_code == HTTPStatus.NOT_FOUND

def test_delete_course_fail_as_student(client: TestClient):
    # Setup: Teacher creates a course
    teacher_unique_suffix = uuid.uuid4().hex[:8]
    teacher_signup_data = {"username": f"t_delete_{teacher_unique_suffix}@example.com", "display_name": "T Delete", "role": "teacher", "password": "password"}
    client.post("/api/v1/users/signup", json=teacher_signup_data)
    login_response_teacher = client.post("/api/v1/users/login", json={"username": teacher_signup_data["username"], "password": "password"})
    assert login_response_teacher.status_code == HTTPStatus.OK
    
    course_payload = create_unique_course_payload(course_template_1)
    create_response = client.post("/api/v1/courses/", json=course_payload)
    assert create_response.status_code == HTTPStatus.CREATED
    course_id = create_response.json()["id"]

    # Action: Student attempts to delete
    student_unique_suffix = uuid.uuid4().hex[:8]
    student_signup_data = {"username": f"s_delete_{student_unique_suffix}@example.com", "display_name": "S Delete", "role": "student", "password": "password"}
    client.post("/api/v1/users/signup", json=student_signup_data)
    login_response_student = client.post("/api/v1/users/login", json={"username": student_signup_data["username"], "password": "password"})
    assert login_response_student.status_code == HTTPStatus.OK

    response = client.delete(f"/api/v1/courses/{course_id}")
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "Teacher role required" in response.json()["detail"]

def test_delete_course_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00" # A valid ObjectId format but unlikely to exist
    response = client.delete(f"/api/v1/courses/{non_existent_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND