# FilePath: api/tests/test_qca_routes.py
from fastapi.testclient import TestClient
from http import HTTPStatus
import uuid

# Import necessary data types and enums
from app.questions.data_types import AnswerTypeEnum
from app.qca.data_types import AnswerAssociationTypeEnum
from app.courses.data_types import CourseCreate # To create courses for testing
from app.questions.data_types import QuestionCreate # To create questions for testing

# Helper to create a unique course for testing QCA
def create_test_course(client: TestClient, suffix: str) -> dict:
    course_payload = {
        "name": f"Test Course for QCA {suffix}",
        "code": f"QCA_CRS_{suffix}",
        "description": "A test course."
    }
    response = client.post("/api/v1/courses/", json=course_payload)
    assert response.status_code == HTTPStatus.CREATED, f"Failed to create test course: {response.text}"
    return response.json()

# Helper to create a unique question for testing QCA
def create_test_question(client: TestClient, suffix: str) -> dict:
    question_payload = {
        "title": f"Test Question for QCA {suffix}",
        "answer_type": AnswerTypeEnum.multiple_choice.value,
        "answer_options": {"a": "Opt A", "b": "Opt B"},
        "scoring_rules": {"correct_option_key": "a", "score_if_correct": 1}
    }
    response = client.post("/api/v1/questions/", json=question_payload)
    assert response.status_code == HTTPStatus.CREATED, f"Failed to create test question: {response.text}"
    return response.json()


def test_create_qca_success(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    
    # 1. Create a course and a question first
    course_suffix = uuid.uuid4().hex[:6]
    question_suffix = uuid.uuid4().hex[:6]
    course = create_test_course(client, course_suffix)
    question = create_test_question(client, question_suffix)

    qca_payload = {
        "question_id": question["id"],
        "course_id": course["id"],
        "answer_association_type": AnswerAssociationTypeEnum.positive.value,
        "feedbacks_based_on_score": [
            {"score_value": 0, "comparison": "eq", "feedback": "Specific feedback for this course context."}
        ]
    }
    response = client.post("/api/v1/question-course-associations/", json=qca_payload)
    assert response.status_code == HTTPStatus.CREATED, response.text
    data = response.json()
    assert data["question_id"] == question["id"]
    assert data["course_id"] == course["id"]
    assert data["answer_association_type"] == AnswerAssociationTypeEnum.positive.value
    assert len(data["feedbacks_based_on_score"]) == 1
    assert data["feedbacks_based_on_score"][0]["feedback"] == "Specific feedback for this course context."

def test_create_qca_fail_duplicate(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    course = create_test_course(client, uuid.uuid4().hex[:6])
    question = create_test_question(client, uuid.uuid4().hex[:6])

    qca_payload = {"question_id": question["id"], "course_id": course["id"]}
    client.post("/api/v1/question-course-associations/", json=qca_payload) # First time
    response = client.post("/api/v1/question-course-associations/", json=qca_payload) # Duplicate
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "already associated" in response.json()["detail"]

def test_create_qca_fail_invalid_question_id(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    course = create_test_course(client, uuid.uuid4().hex[:6])
    qca_payload = {"question_id": "60c72b2f9b1e8b001c8e4d00", "course_id": course["id"]} # Non-existent question
    response = client.post("/api/v1/question-course-associations/", json=qca_payload)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "Question with ID" in response.json()["detail"]

def test_create_qca_fail_invalid_course_id(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    question = create_test_question(client, uuid.uuid4().hex[:6])
    qca_payload = {"question_id": question["id"], "course_id": "60c72b2f9b1e8b001c8e4d01"} # Non-existent course
    response = client.post("/api/v1/question-course-associations/", json=qca_payload)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "Course with ID" in response.json()["detail"]


def test_create_qca_fail_as_student(
    # We still need the fixtures to create the users
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    # Get the shared client instance and user details from fixtures
    # The fixtures will run once before this, student will be logged in last by fixture execution.
    # We will override this.
    client, teacher_details_from_fixture = authenticated_teacher_data_and_client
    _, student_details_from_fixture = authenticated_student_data_and_client # client is the same instance

    # --- Teacher's turn ---
    teacher_login_payload = {"username": teacher_details_from_fixture["username"], "password": "testpassword"}
    login_res_teacher = client.post("/api/v1/users/login", json=teacher_login_payload)
    assert login_res_teacher.status_code == HTTPStatus.OK, f"Teacher login failed: {login_res_teacher.text}"
    
    # Verify teacher is logged in
    me_response_teacher = client.get("/api/v1/users/me")
    assert me_response_teacher.status_code == HTTPStatus.OK
    assert me_response_teacher.json()["username"] == teacher_details_from_fixture["username"]

    # Create prerequisite resources
    course = create_test_course(client, uuid.uuid4().hex[:6]) # Use the shared client
    question = create_test_question(client, uuid.uuid4().hex[:6]) # Use the shared client

    # --- Student's turn ---
    # No need to logout first if the new login correctly establishes a new session and cookie.
    # If issues persisted, an explicit logout here would be the next step.
    student_login_payload = {"username": student_details_from_fixture["username"], "password": "testpassword"}
    login_res_student = client.post("/api/v1/users/login", json=student_login_payload)
    assert login_res_student.status_code == HTTPStatus.OK, f"Student login failed: {login_res_student.text}"

    # Verify student is logged in
    me_response_student = client.get("/api/v1/users/me")
    assert me_response_student.status_code == HTTPStatus.OK
    assert me_response_student.json()["username"] == student_details_from_fixture["username"]
    
    # Perform the action as student
    qca_payload = {"question_id": question["id"], "course_id": course["id"]}
    
    response = client.post("/api/v1/question-course-associations/", json=qca_payload) # Use the shared client

    assert response.status_code == HTTPStatus.FORBIDDEN

    try:
        detail = response.json()["detail"]
        assert "Teacher role required" in detail
    except (KeyError, TypeError, AttributeError):
        assert False, "Response JSON did not contain 'detail', was not valid JSON, or 'detail' was not a string."


def test_list_qcas_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    course1 = create_test_course(client, "c1")
    course2 = create_test_course(client, "c2")
    question1 = create_test_question(client, "q1")
    question2 = create_test_question(client, "q2")

    qca1_payload = {"question_id": question1["id"], "course_id": course1["id"]}
    client.post("/api/v1/question-course-associations/", json=qca1_payload)
    qca2_payload = {"question_id": question2["id"], "course_id": course1["id"]} # q2 also with course1
    client.post("/api/v1/question-course-associations/", json=qca2_payload)
    qca3_payload = {"question_id": question1["id"], "course_id": course2["id"]} # q1 also with course2
    client.post("/api/v1/question-course-associations/", json=qca3_payload)

    # List all
    response_all = client.get("/api/v1/question-course-associations/")
    assert response_all.status_code == HTTPStatus.OK
    data_all = response_all.json()
    assert isinstance(data_all, list)
    assert len(data_all) >= 3

    # Filter by course_id
    response_course1 = client.get(f"/api/v1/question-course-associations/?course_id={course1['id']}")
    assert response_course1.status_code == HTTPStatus.OK
    data_course1 = response_course1.json()
    assert len(data_course1) == 2
    q_ids_in_course1 = {item["question_id"] for item in data_course1}
    assert question1["id"] in q_ids_in_course1
    assert question2["id"] in q_ids_in_course1

    # Filter by question_id
    response_question1 = client.get(f"/api/v1/question-course-associations/?question_id={question1['id']}")
    assert response_question1.status_code == HTTPStatus.OK
    data_question1 = response_question1.json()
    assert len(data_question1) == 2
    c_ids_for_question1 = {item["course_id"] for item in data_question1}
    assert course1["id"] in c_ids_for_question1
    assert course2["id"] in c_ids_for_question1

def test_get_qca_by_id_success(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    course = create_test_course(client, uuid.uuid4().hex[:6])
    question = create_test_question(client, uuid.uuid4().hex[:6])
    qca_payload = {"question_id": question["id"], "course_id": course["id"]}
    create_res = client.post("/api/v1/question-course-associations/", json=qca_payload)
    qca_id = create_res.json()["id"]

    response = client.get(f"/api/v1/question-course-associations/{qca_id}")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == qca_id
    assert data["question_id"] == question["id"]
    assert data["course_id"] == course["id"]

def test_get_qca_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    response = client.get(f"/api/v1/question-course-associations/{non_existent_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_update_qca_success(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    course = create_test_course(client, uuid.uuid4().hex[:6])
    question = create_test_question(client, uuid.uuid4().hex[:6])
    qca_payload = {
        "question_id": question["id"],
        "course_id": course["id"],
        "answer_association_type": AnswerAssociationTypeEnum.positive.value
    }
    create_res = client.post("/api/v1/question-course-associations/", json=qca_payload)
    qca_id = create_res.json()["id"]

    update_data = {
        "answer_association_type": AnswerAssociationTypeEnum.negative.value,
        "feedbacks_based_on_score": [{"score_value": 1, "comparison": "eq", "feedback": "Updated feedback"}]
    }
    response = client.put(f"/api/v1/question-course-associations/{qca_id}", json=update_data)
    assert response.status_code == HTTPStatus.OK, response.text
    data = response.json()
    assert data["answer_association_type"] == AnswerAssociationTypeEnum.negative.value
    assert len(data["feedbacks_based_on_score"]) == 1
    assert data["feedbacks_based_on_score"][0]["feedback"] == "Updated feedback"

def test_update_qca_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    update_data = {"answer_association_type": AnswerAssociationTypeEnum.negative.value}
    response = client.put(f"/api/v1/question-course-associations/{non_existent_id}", json=update_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_delete_qca_success(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    course = create_test_course(client, uuid.uuid4().hex[:6])
    question = create_test_question(client, uuid.uuid4().hex[:6])
    qca_payload = {"question_id": question["id"], "course_id": course["id"]}
    create_res = client.post("/api/v1/question-course-associations/", json=qca_payload)
    qca_id = create_res.json()["id"]

    delete_response = client.delete(f"/api/v1/question-course-associations/{qca_id}")
    assert delete_response.status_code == HTTPStatus.NO_CONTENT

    get_response = client.get(f"/api/v1/question-course-associations/{qca_id}")
    assert get_response.status_code == HTTPStatus.NOT_FOUND

def test_delete_qca_not_found(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_teacher_data_and_client
    non_existent_id = "60c72b2f9b1e8b001c8e4d00"
    response = client.delete(f"/api/v1/question-course-associations/{non_existent_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND
    