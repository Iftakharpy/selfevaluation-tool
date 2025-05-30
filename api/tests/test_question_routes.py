# FilePath: api/tests/test_question_routes.py
from fastapi.testclient import TestClient
from http import HTTPStatus
import uuid 

from app.questions.data_types import AnswerTypeEnum

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

def test_create_question_fail_unauthenticated(client: TestClient): # Uses function-scoped client
    question_payload = create_base_question_payload(AnswerTypeEnum.range)
    response = client.post("/api/v1/questions/", json=question_payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_create_question_invalid_payload(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    invalid_payload = {"title": "Sh", "answer_type": "invalid_type"} # title too short, invalid enum
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
    print(f"\n--- test_update_question_success: Client cookies at start: {client.cookies.items()} ---")
    print(f"--- Authenticated as: {teacher_details['username']} ---")
            
    unique_suffix_create = uuid.uuid4().hex[:6]
    original_payload = create_base_question_payload(AnswerTypeEnum.multiple_select, unique_suffix_create)
    
    create_response = client.post("/api/v1/questions/", json=original_payload)
    assert create_response.status_code == HTTPStatus.CREATED, f"Create failed: {create_response.text} - Cookies: {client.cookies.items()}"
    question_id = create_response.json()["id"]

    unique_suffix_update = uuid.uuid4().hex[:4]
    update_data_payload = {"title": f"Updated Title {unique_suffix_update}", "details": "Updated details."}
    
    print(f"--- test_update_question_success: Client cookies before PUT: {client.cookies.items()} ---")
    response = client.put(f"/api/v1/questions/{question_id}", json=update_data_payload)
    
    if response.status_code != HTTPStatus.OK:
        print(f"\nDEBUG: test_update_question_success - PUT request failed for question ID {question_id}")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response JSON: {response.json()}")
        except Exception:
            print(f"Response Text: {response.text}")
        print("Request Payload Sent for PUT:")
        print(update_data_payload)
        print(f"--- test_update_question_success: Client cookies after failed PUT: {client.cookies.items()} ---")

    assert response.status_code == HTTPStatus.OK
    
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