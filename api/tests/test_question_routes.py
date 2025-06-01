# FilePath: C:\Users\iftak\Desktop\jamk\2025 Spring\narsus-self-evaluation-tool\api\tests\test_question_routes.py
# FilePath: api/tests/test_question_routes.py
from fastapi.testclient import TestClient
from http import HTTPStatus
import uuid 

from app.questions.data_types import AnswerTypeEnum
from app.courses.data_types import CourseCreate # For creating courses for QCA test

# --- Test Data Templates ---
def create_base_question_payload(answer_type: AnswerTypeEnum, unique_suffix: str = ""):
    title = f"Sample Question {answer_type.value} {unique_suffix}"
    payload = {
        "title": title,
        "details": f"Some details for {title}",
        "answer_type": answer_type.value,
        "answer_options": None,
        "scoring_rules": {},
        "default_feedbacks_on_score": [
            {"score_value": 0, "comparison": "lte", "feedback": "Needs significant improvement."},
            {"score_value": 3, "comparison": "gt", "feedback": "Good understanding."}
        ]
    }
    if answer_type == AnswerTypeEnum.multiple_choice:
        payload["answer_options"] = {"a": "Option A", "b": "Option B", "c": "Correct Option C"}
        payload["scoring_rules"] = {"correct_option_key": "c", "score_if_correct": 5, "score_if_incorrect": 0}
    elif answer_type == AnswerTypeEnum.multiple_select:
        payload["answer_options"] = {"a": "Option A", "b": "Correct B", "c": "Correct C", "d": "Option D"}
        payload["scoring_rules"] = {"correct_option_keys": ["b", "c"], "score_per_correct": 2, "penalty_per_incorrect": -1}
    elif answer_type == AnswerTypeEnum.input:
        payload["answer_options"] = {"max_length": 100} 
        payload["scoring_rules"] = {"expected_answers": [{"text": "OpenAI", "score": 5, "case_sensitive": False}], "default_incorrect_score": 0}
    elif answer_type == AnswerTypeEnum.range:
        payload["answer_options"] = {"min": 1, "max": 10, "step": 1}
        payload["scoring_rules"] = {"target_value": 7, "score_at_target": 10, "score_per_deviation_unit": -1}
    return payload

# Helper to create a course for testing QCA cascade
def create_test_course_for_question_test(client: TestClient, suffix: str) -> dict:
    course_payload = {
        "name": f"Test Course QDT {suffix}", # Shortened name
        "code": f"CRSQD_{suffix}", # Shortened code CRS_Q_DEL_ -> CRSQD_ (10 + 6 = 16 chars) - OK
        "description": "A test course."
    }
    response = client.post("/api/v1/courses/", json=course_payload)
    assert response.status_code == HTTPStatus.CREATED, f"Failed to create test course: {response.text}"
    return response.json()

# Helper to create a QCA
def create_test_qca_for_question_test(client: TestClient, question_id: str, course_id: str) -> dict:
    qca_payload = {
        "question_id": question_id,
        "course_id": course_id,
    }
    response = client.post("/api/v1/question-course-associations/", json=qca_payload)
    assert response.status_code == HTTPStatus.CREATED, f"Failed to create QCA: {response.text}"
    return response.json()


def test_create_question_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    unique_suffix = uuid.uuid4().hex[:6]
    question_payload = create_base_question_payload(AnswerTypeEnum.multiple_choice, unique_suffix)

    response = client.post("/api/v1/questions/", json=question_payload)
    
    assert response.status_code == HTTPStatus.CREATED, response.text
    data = response.json()
    assert data["title"] == question_payload["title"]
    assert data["answer_type"] == question_payload["answer_type"]
    assert "id" in data
    assert data["answer_options"] == question_payload["answer_options"]
    assert data["scoring_rules"] == question_payload["scoring_rules"]

def test_create_question_fail_as_student(authenticated_student_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_student_data_and_client
    question_payload = create_base_question_payload(AnswerTypeEnum.input)
    
    response = client.post("/api/v1/questions/", json=question_payload)
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_create_question_fail_unauthenticated(client: TestClient): 
    question_payload = create_base_question_payload(AnswerTypeEnum.range)
    response = client.post("/api/v1/questions/", json=question_payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_create_question_invalid_payload(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    invalid_payload = {"title": "Sh", "answer_type": "invalid_type"} 
    response = client.post("/api/v1/questions/", json=invalid_payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY 

# --- List Questions Tests ---
def test_list_questions_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    q1_payload = create_base_question_payload(AnswerTypeEnum.multiple_choice, uuid.uuid4().hex[:6])
    q2_payload = create_base_question_payload(AnswerTypeEnum.input, uuid.uuid4().hex[:6])
    res1 = client.post("/api/v1/questions/", json=q1_payload)
    assert res1.status_code == HTTPStatus.CREATED, res1.text
    res2 = client.post("/api/v1/questions/", json=q2_payload)
    assert res2.status_code == HTTPStatus.CREATED, res2.text

    response = client.get("/api/v1/questions/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2 
    
    titles = [q["title"] for q in data]
    assert q1_payload["title"] in titles
    assert q2_payload["title"] in titles

def test_list_questions_fail_as_student(authenticated_student_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_student_data_and_client
    response = client.get("/api/v1/questions/")
    assert response.status_code == HTTPStatus.FORBIDDEN

# --- Get Question by ID Tests ---
def test_get_question_by_id_success(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    question_payload = create_base_question_payload(AnswerTypeEnum.range, uuid.uuid4().hex[:6])
    create_response = client.post("/api/v1/questions/", json=question_payload)
    assert create_response.status_code == HTTPStatus.CREATED, create_response.text
    question_id = create_response.json()["id"]

    response = client.get(f"/api/v1/questions/{question_id}")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == question_id
    assert data["title"] == question_payload["title"]

def test_get_question_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00" 
    response = client.get(f"/api/v1/questions/{non_existent_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_get_question_invalid_id_format(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    response = client.get("/api/v1/questions/invalid-id")
    assert response.status_code == HTTPStatus.BAD_REQUEST

# --- Update Question Tests ---
def test_update_question_success(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, teacher_details = authenticated_teacher_data_and_client
            
    unique_suffix_create = uuid.uuid4().hex[:6]
    original_payload = create_base_question_payload(AnswerTypeEnum.multiple_select, unique_suffix_create)
    
    create_response = client.post("/api/v1/questions/", json=original_payload)
    assert create_response.status_code == HTTPStatus.CREATED, f"Create failed: {create_response.text}"
    question_id = create_response.json()["id"]

    unique_suffix_update = uuid.uuid4().hex[:4]
    update_data_payload = {"title": f"Updated Title {unique_suffix_update}", "details": "Updated details."}
    
    response = client.put(f"/api/v1/questions/{question_id}", json=update_data_payload)
    
    assert response.status_code == HTTPStatus.OK, response.text
    
    data = response.json()
    assert data["id"] == question_id
    assert data["title"] == update_data_payload["title"]
    assert data["details"] == update_data_payload["details"]
    assert data["answer_type"] == original_payload["answer_type"]
    assert data["answer_options"] == original_payload["answer_options"]
    assert data["scoring_rules"] == original_payload["scoring_rules"]

def test_update_question_no_change(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    original_payload = create_base_question_payload(AnswerTypeEnum.input, uuid.uuid4().hex[:6])
    create_response = client.post("/api/v1/questions/", json=original_payload)
    assert create_response.status_code == HTTPStatus.CREATED, create_response.text
    question_id = create_response.json()["id"]

    update_data = {"title": original_payload["title"]} 
    response = client.put(f"/api/v1/questions/{question_id}", json=update_data)
    assert response.status_code == HTTPStatus.OK 
    data = response.json()
    assert data["title"] == original_payload["title"]

def test_update_question_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    update_data = {"title": "Non Existent Update"}
    response = client.put(f"/api/v1/questions/{non_existent_id}", json=update_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_update_question_empty_payload(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    original_payload = create_base_question_payload(AnswerTypeEnum.input, uuid.uuid4().hex[:6])
    create_response = client.post("/api/v1/questions/", json=original_payload)
    assert create_response.status_code == HTTPStatus.CREATED, create_response.text
    question_id = create_response.json()["id"]

    response = client.put(f"/api/v1/questions/{question_id}", json={}) 
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "No update data provided" in response.json()["detail"]

# --- Delete Question Tests ---
def test_delete_question_success(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    question_payload = create_base_question_payload(AnswerTypeEnum.range, uuid.uuid4().hex[:6])
    create_response = client.post("/api/v1/questions/", json=question_payload)
    assert create_response.status_code == HTTPStatus.CREATED, create_response.text
    question_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/questions/{question_id}")
    assert delete_response.status_code == HTTPStatus.NO_CONTENT

    get_response = client.get(f"/api/v1/questions/{question_id}")
    assert get_response.status_code == HTTPStatus.NOT_FOUND

def test_delete_question_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    response = client.delete(f"/api/v1/questions/{non_existent_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND

# --- NEW TEST FOR QCA CASCADE ---
def test_delete_question_cascades_to_qca(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client # client is authed as teacher

    # 1. Create a course and a question
    course = create_test_course_for_question_test(client, "CFCasc") # client is teacher
    assert course is not None
    course_id = course["id"]

    question_payload = create_base_question_payload(AnswerTypeEnum.input, uuid.uuid4().hex[:6])
    question_res = client.post("/api/v1/questions/", json=question_payload) # client is teacher
    assert question_res.status_code == HTTPStatus.CREATED
    question_id = question_res.json()["id"]
    
    # 2. Create a QCA linking them
    qca = create_test_qca_for_question_test(client, question_id, course_id) # client is teacher
    assert qca is not None
    qca_id = qca["id"]

    # 3. Verify QCA exists
    get_qca_res = client.get(f"/api/v1/question-course-associations/{qca_id}") # client is teacher
    assert get_qca_res.status_code == HTTPStatus.OK

    # 4. Delete the question
    delete_question_res = client.delete(f"/api/v1/questions/{question_id}") # client is teacher
    assert delete_question_res.status_code == HTTPStatus.NO_CONTENT

    # 5. Verify QCA is deleted
    get_qca_after_delete_res = client.get(f"/api/v1/question-course-associations/{qca_id}") # client is teacher
    assert get_qca_after_delete_res.status_code == HTTPStatus.NOT_FOUND