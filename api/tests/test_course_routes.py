from fastapi.testclient import TestClient
from http import HTTPStatus
import uuid

from app.questions.data_types import AnswerTypeEnum

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
    unique_suffix = uuid.uuid4().hex[:6]
    payload = base_payload.copy()
    payload["code"] = f"{base_payload['code']}_{unique_suffix}"
    return payload

def create_test_question_for_course_test(client: TestClient, suffix: str) -> dict:
    question_payload = {
        "title": f"Test Question for Course Deletion Test {suffix}",
        "answer_type": AnswerTypeEnum.multiple_choice.value,
        "answer_options": {"a": "Opt A", "b": "Opt B"},
        "scoring_rules": {"correct_option_key": "a", "score_if_correct": 1}
    }
    response = client.post("/api/v1/questions/", json=question_payload)
    assert response.status_code == HTTPStatus.CREATED, f"Failed to create test question: {response.text}"
    return response.json()

def create_test_qca_for_course_test(client: TestClient, question_id: str, course_id: str) -> dict:
    qca_payload = {
        "question_id": question_id,
        "course_id": course_id,
    }
    response = client.post("/api/v1/question-course-associations/", json=qca_payload)
    assert response.status_code == HTTPStatus.CREATED, f"Failed to create QCA: {response.text}"
    return response.json()

def create_test_survey_for_course_test(client: TestClient, course_ids: list, title_suffix: str) -> dict:
    survey_payload = {
        "title": f"Test Survey for Course Deletion {title_suffix}",
        "course_ids": course_ids,
        "is_published": False
    }
    response = client.post("/api/v1/surveys/", json=survey_payload)
    assert response.status_code == HTTPStatus.CREATED, f"Failed to create survey: {response.text}"
    return response.json()


def test_create_course_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client 
    unique_course_payload = create_unique_course_payload(course_template_1)
    response = teacher_client.post("/api/v1/courses/", json=unique_course_payload)
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["name"] == unique_course_payload["name"]
    assert data["code"] == unique_course_payload["code"]
    assert "id" in data

def test_create_course_fail_as_student(authenticated_student_data_and_client: tuple[TestClient, dict]):
    student_client, _ = authenticated_student_data_and_client
    unique_course_payload = create_unique_course_payload(course_template_1)
    response = student_client.post("/api/v1/courses/", json=unique_course_payload)
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "Teacher role required" in response.json()["detail"]

def test_create_course_fail_unauthenticated(client: TestClient): # Uses unauthenticated client
    unique_course_payload = create_unique_course_payload(course_template_1)
    response = client.post("/api/v1/courses/", json=unique_course_payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]

def test_create_course_duplicate_code(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client
    unique_course_payload = create_unique_course_payload(course_template_1)
    response1 = teacher_client.post("/api/v1/courses/", json=unique_course_payload)
    assert response1.status_code == HTTPStatus.CREATED
    response2 = teacher_client.post("/api/v1/courses/", json=unique_course_payload)
    assert response2.status_code == HTTPStatus.BAD_REQUEST
    assert "already exists" in response2.json()["detail"]

def test_list_courses_as_student(
    authenticated_student_data_and_client: tuple[TestClient, dict],
    authenticated_teacher_data_and_client: tuple[TestClient, dict]
):
    teacher_client, _ = authenticated_teacher_data_and_client
    course1_payload = create_unique_course_payload(course_template_1)
    course2_payload = create_unique_course_payload(course_template_2)
    res1 = teacher_client.post("/api/v1/courses/", json=course1_payload)
    assert res1.status_code == HTTPStatus.CREATED
    res2 = teacher_client.post("/api/v1/courses/", json=course2_payload)
    assert res2.status_code == HTTPStatus.CREATED

    student_client, _ = authenticated_student_data_and_client
    response = student_client.get("/api/v1/courses/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)
    retrieved_codes = {item["code"] for item in data}
    assert course1_payload["code"] in retrieved_codes
    assert course2_payload["code"] in retrieved_codes
    assert len(data) >= 2

def test_list_courses_unauthenticated(client: TestClient):
    response = client.get("/api/v1/courses/")
    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_get_course_by_id_success(
    authenticated_student_data_and_client: tuple[TestClient, dict],
    authenticated_teacher_data_and_client: tuple[TestClient, dict]
):
    teacher_client, _ = authenticated_teacher_data_and_client
    unique_course_payload = create_unique_course_payload(course_template_1)
    create_response = teacher_client.post("/api/v1/courses/", json=unique_course_payload)
    assert create_response.status_code == HTTPStatus.CREATED
    course_id = create_response.json()["id"]

    student_client, _ = authenticated_student_data_and_client
    response = student_client.get(f"/api/v1/courses/{course_id}")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == course_id
    assert data["name"] == unique_course_payload["name"]

def test_get_course_not_found(authenticated_student_data_and_client: tuple[TestClient, dict]):
    student_client, _ = authenticated_student_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    response = student_client.get(f"/api/v1/courses/{non_existent_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_get_course_invalid_id_format(authenticated_student_data_and_client: tuple[TestClient, dict]):
    student_client, _ = authenticated_student_data_and_client
    response = student_client.get("/api/v1/courses/invalid-objectid-format")
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_update_course_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client
    original_course_payload = create_unique_course_payload(course_template_1)
    create_response = teacher_client.post("/api/v1/courses/", json=original_course_payload)
    assert create_response.status_code == HTTPStatus.CREATED
    course_id = create_response.json()["id"]
    update_payload = {"name": "Updated Course Name", "description": "Updated description."}
    response = teacher_client.put(f"/api/v1/courses/{course_id}", json=update_payload)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == update_payload["name"]

def test_update_course_fail_as_student(
    authenticated_teacher_data_and_client: tuple[TestClient, dict], 
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    client, teacher_details = authenticated_teacher_data_and_client
    _, student_details = authenticated_student_data_and_client

    # --- Teacher's turn ---
    teacher_login_payload = {"username": teacher_details["username"], "password": "testpassword"}
    login_res_teacher = client.post("/api/v1/users/login", json=teacher_login_payload)
    assert login_res_teacher.status_code == HTTPStatus.OK, f"Teacher login failed: {login_res_teacher.text}"

    course_payload = create_unique_course_payload(course_template_1)
    create_response = client.post("/api/v1/courses/", json=course_payload)
    assert create_response.status_code == HTTPStatus.CREATED, f"Course creation by teacher failed: {create_response.text}"
    course_id = create_response.json()["id"]

    # --- Student's turn ---
    student_login_payload = {"username": student_details["username"], "password": "testpassword"}
    login_res_student = client.post("/api/v1/users/login", json=student_login_payload)
    assert login_res_student.status_code == HTTPStatus.OK, f"Student login failed: {login_res_student.text}"

    update_payload = {"name": "Student Attempt Update"}
    response = client.put(f"/api/v1/courses/{course_id}", json=update_payload)
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_update_course_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    update_payload = {"name": "Attempt Update Non Existent"}
    response = teacher_client.put(f"/api/v1/courses/{non_existent_id}", json=update_payload)
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_update_course_duplicate_code_on_update(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client
    course1_unique = create_unique_course_payload(course_template_1)
    teacher_client.post("/api/v1/courses/", json=course1_unique)
    course2_payload = create_unique_course_payload(course_template_2)
    create_res_2 = teacher_client.post("/api/v1/courses/", json=course2_payload)
    course_2_id = create_res_2.json()["id"]
    update_payload = {"code": course1_unique["code"]}
    response = teacher_client.put(f"/api/v1/courses/{course_2_id}", json=update_payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_delete_course_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client
    unique_course_payload = create_unique_course_payload(course_template_1)
    create_response = teacher_client.post("/api/v1/courses/", json=unique_course_payload)
    course_id = create_response.json()["id"]
    delete_response = teacher_client.delete(f"/api/v1/courses/{course_id}")
    assert delete_response.status_code == HTTPStatus.NO_CONTENT
    get_response = teacher_client.get(f"/api/v1/courses/{course_id}")
    assert get_response.status_code == HTTPStatus.NOT_FOUND

def test_delete_course_fail_as_student(
    authenticated_teacher_data_and_client: tuple[TestClient, dict], 
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    client, teacher_details = authenticated_teacher_data_and_client
    _, student_details = authenticated_student_data_and_client

    # --- Teacher's turn ---
    teacher_login_payload = {"username": teacher_details["username"], "password": "testpassword"}
    login_res_teacher = client.post("/api/v1/users/login", json=teacher_login_payload)
    assert login_res_teacher.status_code == HTTPStatus.OK, f"Teacher login failed: {login_res_teacher.text}"

    course_payload = create_unique_course_payload(course_template_1)
    create_response = client.post("/api/v1/courses/", json=course_payload)
    assert create_response.status_code == HTTPStatus.CREATED, f"Course creation by teacher failed: {create_response.text}"
    course_id = create_response.json()["id"]

    # --- Student's turn ---
    student_login_payload = {"username": student_details["username"], "password": "testpassword"}
    login_res_student = client.post("/api/v1/users/login", json=student_login_payload)
    assert login_res_student.status_code == HTTPStatus.OK, f"Student login failed: {login_res_student.text}"
    
    response = client.delete(f"/api/v1/courses/{course_id}")
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_delete_course_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    response = teacher_client.delete(f"/api/v1/courses/{non_existent_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_delete_course_fails_if_in_survey(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client
    course_payload = create_unique_course_payload(course_template_1)
    course_res = teacher_client.post("/api/v1/courses/", json=course_payload)
    course_id = course_res.json()["id"]
    create_test_survey_for_course_test(teacher_client, [course_id], "DelPrev")
    delete_response = teacher_client.delete(f"/api/v1/courses/{course_id}")
    assert delete_response.status_code == HTTPStatus.BAD_REQUEST
    get_res = teacher_client.get(f"/api/v1/courses/{course_id}")
    assert get_res.status_code == HTTPStatus.OK

def test_delete_course_cascades_to_qca(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client
    course_payload = create_unique_course_payload(course_template_1)
    course_res = teacher_client.post("/api/v1/courses/", json=course_payload)
    course_id = course_res.json()["id"]
    question = create_test_question_for_course_test(teacher_client, "QForCascade")
    question_id = question["id"]
    qca = create_test_qca_for_course_test(teacher_client, question_id, course_id)
    qca_id = qca["id"]
    get_qca_res = teacher_client.get(f"/api/v1/question-course-associations/{qca_id}")
    assert get_qca_res.status_code == HTTPStatus.OK
    teacher_client.delete(f"/api/v1/courses/{course_id}")
    get_qca_after_delete_res = teacher_client.get(f"/api/v1/question-course-associations/{qca_id}")
    assert get_qca_after_delete_res.status_code == HTTPStatus.NOT_FOUND
