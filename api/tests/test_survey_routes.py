# FilePath: C:\Users\iftak\Desktop\jamk\2025 Spring\narsus-self-evaluation-tool\api\tests\test_survey_routes.py
# FilePath: api/tests/test_survey_routes.py
from fastapi.testclient import TestClient
from http import HTTPStatus
import uuid 
from bson import ObjectId 

# Helper functions from other test files (or a shared conftest/utils)

def create_sample_course_for_survey_test(client: TestClient, suffix: str):
    # This client MUST be authenticated as a teacher
    course_payload = {"name": f"CourseSvy {suffix}", "code": f"CRSSVY{suffix}", "description": "A test course for survey."}
    response = client.post("/api/v1/courses/", json=course_payload)
    user_info = "Unauthed/Error" 
    try:
        me_res = client.get('/api/v1/users/me')
        if me_res.is_success: 
            user_info = me_res.json().get('username', 'UnknownUser')
    except Exception: 
        pass
    assert response.status_code == HTTPStatus.CREATED, f"Course creation for survey test failed: {response.text} (User: {user_info})"
    return response.json()

def create_sample_question_for_survey_test(client: TestClient, suffix: str):
    # This client MUST be authenticated as a teacher
    question_payload = {
        "title": f"SampleQSvy {suffix}", "answer_type": "multiple_choice",
        "answer_options": {"a": "Opt A"}, "scoring_rules": {"correct_option_key": "a"}
    }
    q_res = client.post("/api/v1/questions/", json=question_payload)
    assert q_res.status_code == HTTPStatus.CREATED
    return q_res.json()

def create_sample_qca_for_survey_test(client: TestClient, q_id: str, c_id: str):
    # This client MUST be authenticated as a teacher
    qca_payload = {"question_id": q_id, "course_id": c_id}
    qca_res = client.post("/api/v1/question-course-associations/", json=qca_payload)
    assert qca_res.status_code == HTTPStatus.CREATED
    return qca_res.json()

def create_sample_survey_for_test(client: TestClient, course_ids: list, title_suffix: str, published: bool = True):
    # This client MUST be authenticated as a teacher
    survey_payload = {
        "title": f"SurveyTest {title_suffix}",
        "description": "Test survey description.",
        "course_ids": course_ids,
        "is_published": published
    }
    response = client.post("/api/v1/surveys/", json=survey_payload)
    assert response.status_code == HTTPStatus.CREATED, f"Survey creation failed: {response.text}"
    return response.json()

def create_survey_attempt_for_test(client: TestClient, survey_id: str):
    # This client MUST be authenticated as the student.
    start_payload = {"survey_id": survey_id}
    response_start = client.post("/api/v1/survey-attempts/start", json=start_payload)
    assert response_start.status_code == HTTPStatus.OK, response_start.text
    return response_start.json() 

def submit_survey_attempt_for_test(client: TestClient, attempt_id: str):
    # This client MUST be authenticated as the student who owns the attempt.
    response_submit = client.post(f"/api/v1/survey-attempts/{attempt_id}/submit")
    assert response_submit.status_code == HTTPStatus.OK, response_submit.text
    return response_submit.json()


def test_create_survey_success_as_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, teacher_info = authenticated_teacher_data_and_client 
    course1 = create_sample_course_for_survey_test(teacher_client, uuid.uuid4().hex[:4]) 
    course2 = create_sample_course_for_survey_test(teacher_client, uuid.uuid4().hex[:4]) 
    survey_payload = {
        "title": "Teacher's New Awesome Survey",
        "description": "A detailed survey description for testing.",
        "course_ids": [course1["id"], course2["id"]], 
        "is_published": False
    }
    response = teacher_client.post("/api/v1/surveys/", json=survey_payload) 
    assert response.status_code == HTTPStatus.CREATED, response.text
    data = response.json()
    assert data["title"] == survey_payload["title"]
    assert set(data["course_ids"]) == set(survey_payload["course_ids"])
    assert data["created_by"] == teacher_info["id"] 

def test_create_survey_fail_invalid_course_id(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client 
    invalid_course_id = str(ObjectId()) 
    survey_payload = {"title": "Survey Bad Course", "course_ids": [invalid_course_id], "is_published": False}
    response = teacher_client.post("/api/v1/surveys/", json=survey_payload) 
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_create_survey_fail_as_student(
    authenticated_teacher_data_and_client: tuple[TestClient, dict], 
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    teacher_client, teacher_details = authenticated_teacher_data_and_client
    course1 = create_sample_course_for_survey_test(teacher_client, uuid.uuid4().hex[:4]) 

    student_client, student_details = authenticated_student_data_and_client
    
    survey_payload = {"title": "Student Survey Attempt", "course_ids": [course1["id"]], "is_published": False}
    response = student_client.post("/api/v1/surveys/", json=survey_payload) 
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_list_surveys_student_sees_only_published(
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    teacher_client, teacher_details = authenticated_teacher_data_and_client
    course1 = create_sample_course_for_survey_test(teacher_client, uuid.uuid4().hex[:4]) 
    
    pub_title = f"Published Test Survey {uuid.uuid4().hex[:4]}"
    draft_title = f"Draft Test Survey {uuid.uuid4().hex[:4]}"
    
    create_sample_survey_for_test(teacher_client, [course1["id"]], pub_title, published=True) 
    create_sample_survey_for_test(teacher_client, [course1["id"]], draft_title, published=False) 
    
    student_client, student_details = authenticated_student_data_and_client
    response = student_client.get("/api/v1/surveys/") 
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert any(s["title"] == pub_title and s["is_published"] for s in data)
    assert not any(s["title"] == draft_title for s in data)

def test_get_survey_with_questions(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client 
    course = create_sample_course_for_survey_test(teacher_client, f"C_Q_{uuid.uuid4().hex[:4]}")
    question = create_sample_question_for_survey_test(teacher_client, f"Q_Svy_{uuid.uuid4().hex[:4]}")
    create_sample_qca_for_survey_test(teacher_client, question["id"], course["id"])
    
    survey = create_sample_survey_for_test(teacher_client, [course["id"]], "SvyWithQs", published=True)
    
    response = teacher_client.get(f"/api/v1/surveys/{survey['id']}?include_questions=true")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["questions"] is not None and len(data["questions"]) == 1
    assert data["questions"][0]["question_id"] == question["id"]

def test_get_unpublished_survey_by_id_fail_student(
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    teacher_client, teacher_details = authenticated_teacher_data_and_client
    course1 = create_sample_course_for_survey_test(teacher_client, uuid.uuid4().hex[:4]) 
    survey = create_sample_survey_for_test(teacher_client, [course1["id"]], "UnpubSvy", published=False) 
    survey_id = survey["id"]

    student_client, student_details = authenticated_student_data_and_client
    
    response = student_client.get(f"/api/v1/surveys/{survey_id}") 
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_update_survey_success_as_owner_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, teacher_info = authenticated_teacher_data_and_client 
    course1 = create_sample_course_for_survey_test(teacher_client, uuid.uuid4().hex[:4]) 
    survey = create_sample_survey_for_test(teacher_client, [course1["id"]], "OrigTitle", published=False)
    survey_id = survey["id"]

    update_payload = {"title": "Updated Title By Owner", "is_published": True}
    response = teacher_client.put(f"/api/v1/surveys/{survey_id}", json=update_payload) 
    assert response.status_code == HTTPStatus.OK, response.text
    data = response.json()
    assert data["title"] == "Updated Title By Owner"
    assert data["is_published"] is True

def test_delete_survey_success_as_owner_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client 
    course1 = create_sample_course_for_survey_test(teacher_client, uuid.uuid4().hex[:4]) 
    survey = create_sample_survey_for_test(teacher_client, [course1["id"]], "ToDelete")
    survey_id = survey["id"]

    delete_response = teacher_client.delete(f"/api/v1/surveys/{survey_id}") 
    assert delete_response.status_code == HTTPStatus.NO_CONTENT
    get_response = teacher_client.get(f"/api/v1/surveys/{survey_id}") 
    assert get_response.status_code == HTTPStatus.NOT_FOUND

# --- NEW TEST FOR DELETION PREVENTION ---
def test_delete_survey_fails_if_has_submitted_attempts(
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    teacher_client, teacher_details = authenticated_teacher_data_and_client
    course = create_sample_course_for_survey_test(teacher_client, "DelPrevCrsSvy") 
    survey = create_sample_survey_for_test(teacher_client, [course["id"]], "DelPrevSvy", published=True) 
    survey_id = survey["id"]

    student_client, student_details = authenticated_student_data_and_client
    attempt_data = create_survey_attempt_for_test(student_client, survey_id) 
    attempt_id = attempt_data["attempt_id"]
    submit_survey_attempt_for_test(student_client, attempt_id) 

    # Teacher attempts to delete the survey using teacher_client
    delete_response = teacher_client.delete(f"/api/v1/surveys/{survey_id}")
    assert delete_response.status_code == HTTPStatus.BAD_REQUEST
    assert "Cannot delete survey with submitted attempts" in delete_response.json()["detail"]

    # Verify survey still exists using teacher_client
    get_res = teacher_client.get(f"/api/v1/surveys/{survey_id}")
    assert get_res.status_code == HTTPStatus.OK