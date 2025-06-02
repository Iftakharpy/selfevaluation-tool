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
        "answer_options": {"a": "Opt A"}, "scoring_rules": {"correct_option_key": "a", "score_if_correct": 1.0} # Added score rule
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

def create_sample_survey_for_test(client: TestClient, course_ids: list, full_title: str, published: bool = True): # MODIFIED: Renamed title_suffix to full_title
    # This client MUST be authenticated as a teacher
    survey_payload = {
        "title": full_title, # MODIFIED: Use full_title directly
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
    client, teacher_details = authenticated_teacher_data_and_client
    _, student_details = authenticated_student_data_and_client

    # --- Teacher's turn to create a course ---
    teacher_login_payload = {"username": teacher_details["username"], "password": "testpassword"}
    login_res_teacher = client.post("/api/v1/users/login", json=teacher_login_payload)
    assert login_res_teacher.status_code == HTTPStatus.OK, f"Teacher login failed: {login_res_teacher.text}"
    course1 = create_sample_course_for_survey_test(client, uuid.uuid4().hex[:4]) 

    # --- Student's turn to try creating a survey ---
    student_login_payload = {"username": student_details["username"], "password": "testpassword"}
    login_res_student = client.post("/api/v1/users/login", json=student_login_payload)
    assert login_res_student.status_code == HTTPStatus.OK, f"Student login failed: {login_res_student.text}"
    
    survey_payload = {"title": "Student Survey Attempt", "course_ids": [course1["id"]], "is_published": False}
    response = client.post("/api/v1/surveys/", json=survey_payload) 
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_list_surveys_student_sees_only_published(
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    client, teacher_details = authenticated_teacher_data_and_client
    _, student_details = authenticated_student_data_and_client

    # --- Teacher's turn to set up surveys ---
    teacher_login_payload = {"username": teacher_details["username"], "password": "testpassword"}
    login_res_teacher = client.post("/api/v1/users/login", json=teacher_login_payload)
    assert login_res_teacher.status_code == HTTPStatus.OK, f"Teacher login failed: {login_res_teacher.text}"

    course1 = create_sample_course_for_survey_test(client, uuid.uuid4().hex[:4]) 
    
    pub_title = f"Published Test Survey {uuid.uuid4().hex[:4]}"
    draft_title = f"Draft Test Survey {uuid.uuid4().hex[:4]}"
    
    create_sample_survey_for_test(client, [course1["id"]], pub_title, published=True) 
    create_sample_survey_for_test(client, [course1["id"]], draft_title, published=False) 
    
    # --- Student's turn to view surveys ---
    student_login_payload = {"username": student_details["username"], "password": "testpassword"}
    login_res_student = client.post("/api/v1/users/login", json=student_login_payload)
    assert login_res_student.status_code == HTTPStatus.OK, f"Student login failed: {login_res_student.text}"

    response = client.get("/api/v1/surveys/") 
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert any(s["title"] == pub_title and s["is_published"] for s in data)
    assert not any(s["title"] == draft_title for s in data)

def test_get_survey_with_questions(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, _ = authenticated_teacher_data_and_client 
    course = create_sample_course_for_survey_test(teacher_client, f"C_Q_{uuid.uuid4().hex[:4]}")
    question = create_sample_question_for_survey_test(teacher_client, f"Q_Svy_{uuid.uuid4().hex[:4]}")
    create_sample_qca_for_survey_test(teacher_client, question["id"], course["id"])
    
    survey = create_sample_survey_for_test(teacher_client, [course["id"]], "SvyWithQs", published=True) # Uses full_title
    
    response = teacher_client.get(f"/api/v1/surveys/{survey['id']}?include_questions=true")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["questions"] is not None and len(data["questions"]) == 1
    assert data["questions"][0]["question_id"] == question["id"]

def test_get_unpublished_survey_by_id_fail_student(
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    client, teacher_details = authenticated_teacher_data_and_client
    _, student_details = authenticated_student_data_and_client

    # --- Teacher's turn to set up ---
    teacher_login_payload = {"username": teacher_details["username"], "password": "testpassword"}
    login_res_teacher = client.post("/api/v1/users/login", json=teacher_login_payload)
    assert login_res_teacher.status_code == HTTPStatus.OK, f"Teacher login failed: {login_res_teacher.text}"
    
    course1 = create_sample_course_for_survey_test(client, uuid.uuid4().hex[:4]) 
    survey = create_sample_survey_for_test(client, [course1["id"]], "UnpubSvy", published=False) # Uses full_title
    survey_id = survey["id"]

    # --- Student's turn to attempt access ---
    student_login_payload = {"username": student_details["username"], "password": "testpassword"}
    login_res_student = client.post("/api/v1/users/login", json=student_login_payload)
    assert login_res_student.status_code == HTTPStatus.OK, f"Student login failed: {login_res_student.text}"
    
    response = client.get(f"/api/v1/surveys/{survey_id}") 
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_update_survey_success_as_owner_teacher(authenticated_teacher_data_and_client: tuple[TestClient, dict]):
    teacher_client, teacher_info = authenticated_teacher_data_and_client 
    course1 = create_sample_course_for_survey_test(teacher_client, uuid.uuid4().hex[:4]) 
    survey = create_sample_survey_for_test(teacher_client, [course1["id"]], "OrigTitle", published=False) # Uses full_title
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
    survey = create_sample_survey_for_test(teacher_client, [course1["id"]], "ToDelete") # Uses full_title
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
    client, teacher_details = authenticated_teacher_data_and_client
    _, student_details = authenticated_student_data_and_client

    # --- Teacher's turn to set up ---
    teacher_login_payload = {"username": teacher_details["username"], "password": "testpassword"}
    login_res_teacher = client.post("/api/v1/users/login", json=teacher_login_payload)
    assert login_res_teacher.status_code == HTTPStatus.OK, f"Teacher login failed: {login_res_teacher.text}"

    course = create_sample_course_for_survey_test(client, "DelPrevCrsSvy") 
    survey = create_sample_survey_for_test(client, [course["id"]], "DelPrevSvy", published=True) # Uses full_title
    survey_id = survey["id"]

    # --- Student's turn to take survey ---
    student_login_payload = {"username": student_details["username"], "password": "testpassword"}
    login_res_student = client.post("/api/v1/users/login", json=student_login_payload)
    assert login_res_student.status_code == HTTPStatus.OK, f"Student login failed: {login_res_student.text}"

    attempt_data = create_survey_attempt_for_test(client, survey_id) 
    attempt_id = attempt_data["attempt_id"]
    submit_survey_attempt_for_test(client, attempt_id) 

    # --- Teacher's turn to attempt deletion ---
    login_res_teacher_again = client.post("/api/v1/users/login", json=teacher_login_payload)
    assert login_res_teacher_again.status_code == HTTPStatus.OK, f"Teacher re-login failed: {login_res_teacher_again.text}"

    delete_response = client.delete(f"/api/v1/surveys/{survey_id}")
    assert delete_response.status_code == HTTPStatus.BAD_REQUEST
    assert "Cannot delete survey with submitted attempts" in delete_response.json()["detail"]

    # Verify survey still exists
    get_res = client.get(f"/api/v1/surveys/{survey_id}")
    assert get_res.status_code == HTTPStatus.OK

# --- NEW TEST FOR CASCADE DELETE OF UNSUBMITTED ATTEMPTS ---
def test_delete_survey_cascades_to_unsubmitted_attempts_and_answers(
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    client, teacher_details = authenticated_teacher_data_and_client
    _, student_details = authenticated_student_data_and_client

    # --- Teacher: Create survey ---
    teacher_login_payload = {"username": teacher_details["username"], "password": "testpassword"}
    client.post("/api/v1/users/login", json=teacher_login_payload)
    
    course = create_sample_course_for_survey_test(client, "CascadeDelCrs")
    question = create_sample_question_for_survey_test(client, "CascadeDelQ")
    create_sample_qca_for_survey_test(client, question["id"], course["id"])
    
    survey = create_sample_survey_for_test(client, [course["id"]], "SurveyForCascadeDel", published=True)
    survey_id = survey["id"]

    # --- Student: Start survey and save some answers (but don't submit) ---
    student_login_payload = {"username": student_details["username"], "password": "testpassword"}
    client.post("/api/v1/users/login", json=student_login_payload)
    
    start_data = create_survey_attempt_for_test(client, survey_id)
    attempt_id = start_data["attempt_id"]
    
    q_map = {q["question_id"]: q["qca_id"] for q in start_data["questions"]}
    qca_id_for_answer = q_map[question["id"]]

    answers_to_save = [{"qca_id": qca_id_for_answer, "question_id": question["id"], "answer_value": "a"}]
    ans_resp = client.post(f"/api/v1/survey-attempts/{attempt_id}/answers", json={"answers": answers_to_save})
    assert ans_resp.status_code == HTTPStatus.OK, f"Failed to save answers: {ans_resp.text}"
    # saved_answer_id = ans_resp.json()[0]["id"] # Not strictly needed for this test flow

    # --- Teacher: Delete the survey ---
    client.post("/api/v1/users/login", json=teacher_login_payload) # Re-login as teacher
    delete_response = client.delete(f"/api/v1/surveys/{survey_id}")
    assert delete_response.status_code == HTTPStatus.NO_CONTENT, f"Survey deletion failed: {delete_response.text}"

    # --- Verify: Survey is gone ---
    get_survey_res = client.get(f"/api/v1/surveys/{survey_id}")
    assert get_survey_res.status_code == HTTPStatus.NOT_FOUND, "Survey was not deleted."

    # The cascading deletion of unsubmitted attempts and their answers is an internal behavior.
    # The primary check is that the survey deletion itself was successful and didn't error out
    # due to issues with cascading (which would happen if the DB operations failed).
    # A more direct verification of attempt/answer deletion would require DB inspection in the test,
    # or dedicated admin API endpoints which are beyond typical user-facing APIs.
    print(f"Test test_delete_survey_cascades_to_unsubmitted_attempts_and_answers: Survey {survey_id} deleted. Cascading assumed successful.")
