from fastapi.testclient import TestClient
from http import HTTPStatus
import uuid
from bson import ObjectId # For creating dummy ObjectIds

# Helper functions (can be moved to a shared test utility module if not already)
def create_course_for_attempt_test(client: TestClient, suffix: str):
    payload = {"name": f"Course Att {suffix}", "code": f"CRS_ATT_{suffix}", "description": "Test course"}
    response = client.post("/api/v1/courses/", json=payload)
    assert response.status_code == HTTPStatus.CREATED
    return response.json()

def create_question_for_attempt_test(client: TestClient, suffix: str, ans_type: str = "multiple_choice", options: dict = None, rules: dict = None):
    if options is None: options = {"a": "Option A", "b": "Option B"}
    if rules is None: rules = {"correct_option_key": "a", "score_if_correct": 1.0}
    payload = {"title": f"Q Att {suffix}", "answer_type": ans_type, "answer_options": options, "scoring_rules": rules}
    response = client.post("/api/v1/questions/", json=payload)
    assert response.status_code == HTTPStatus.CREATED
    return response.json()

def create_qca_for_attempt_test(client: TestClient, q_id: str, c_id: str):
    payload = {"question_id": q_id, "course_id": c_id}
    response = client.post("/api/v1/question-course-associations/", json=payload)
    assert response.status_code == HTTPStatus.CREATED
    return response.json()

def create_survey_for_attempt_test(client: TestClient, course_ids: list, published: bool = True, title_prefix="Survey Att", score_thresholds: dict = None):
    title = f"{title_prefix} {uuid.uuid4().hex[:4]}"
    payload = {"title": title, "course_ids": course_ids, "is_published": published}
    if score_thresholds:
        payload["course_skill_total_score_thresholds"] = score_thresholds
    response = client.post("/api/v1/surveys/", json=payload)
    assert response.status_code == HTTPStatus.CREATED, response.text
    return response.json()


def test_full_survey_attempt_lifecycle(
    client: TestClient,
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    # --- Teacher Setup ---
    _, teacher_details = authenticated_teacher_data_and_client
    login_res_teacher = client.post("/api/v1/users/login", json={"username": teacher_details["username"], "password": "testpassword"})
    assert login_res_teacher.status_code == HTTPStatus.OK

    course1 = create_course_for_attempt_test(client, "C1_Full")
    question1_mc = create_question_for_attempt_test(client, "Q1MC_Full", ans_type="multiple_choice", options={"a":"Correct","b":"Wrong"}, rules={"correct_option_key":"a", "score_if_correct": 2.0})
    question2_inp = create_question_for_attempt_test(client, "Q2INP_Full", ans_type="input", rules={"expected_answers": [{"text":"test input", "score":3.0, "case_sensitive": False}], "default_incorrect_score":0.0})
    
    qca1 = create_qca_for_attempt_test(client, question1_mc["id"], course1["id"])
    qca2 = create_qca_for_attempt_test(client, question2_inp["id"], course1["id"])
    
    survey_score_thresholds = {
        course1["id"]: [
            {"score_value": 1.0, "comparison": "lt", "feedback": "Course: Needs review"},
            {"score_value": 3.0, "comparison": "gte", "feedback": "Course: Good job!"}
        ]
    }
    survey = create_survey_for_attempt_test(client, [course1["id"]], published=True, title_prefix="Full Lifecycle Survey", score_thresholds=survey_score_thresholds)

    # --- Student Actions ---
    _, student_details = authenticated_student_data_and_client
    login_res_student = client.post("/api/v1/users/login", json={"username": student_details["username"], "password": "testpassword"})
    assert login_res_student.status_code == HTTPStatus.OK

    # 1. Start Survey Attempt
    start_payload = {"survey_id": survey["id"]}
    response_start = client.post("/api/v1/survey-attempts/start", json=start_payload)
    assert response_start.status_code == HTTPStatus.OK, response_start.text
    start_data = response_start.json()
    attempt_id = start_data["attempt_id"]
    assert start_data["survey_id"] == survey["id"]
    assert len(start_data["questions"]) == 2 
    
    q_map = {q["question_id"]: q["qca_id"] for q in start_data["questions"]}

    # 2. Submit Answers
    answers_to_submit = [
        {"qca_id": q_map[question1_mc["id"]], "question_id": question1_mc["id"], "answer_value": "a"}, # Correct -> Score: 2.0
        {"qca_id": q_map[question2_inp["id"]], "question_id": question2_inp["id"], "answer_value": "wrong input"} # Incorrect -> Score: 0.0
    ]
    response_answers = client.post(f"/api/v1/survey-attempts/{attempt_id}/answers", json={"answers": answers_to_submit})
    assert response_answers.status_code == HTTPStatus.OK, response_answers.text
    submitted_answers_data = response_answers.json()
    assert len(submitted_answers_data) == 2

    # 3. Submit Survey
    response_submit = client.post(f"/api/v1/survey-attempts/{attempt_id}/submit")
    assert response_submit.status_code == HTTPStatus.OK, response_submit.text
    submit_result_data = response_submit.json()
    assert submit_result_data["is_submitted"] is True
    assert submit_result_data["id"] == attempt_id
    assert course1["id"] in submit_result_data["course_scores"]
    assert submit_result_data["course_scores"][course1["id"]] == 2.0 # q1=2.0, q2=0.0 -> Total course score = 2.0
    assert course1["id"] in submit_result_data["course_feedback"]
    # Based on total score 2.0 and rule "lt 1.0 -> Needs review", "gte 3.0 -> Good job!", it should pick neither directly defined here.
    # The actual feedback might be the fallback "Please review your performance..." or a more specific one if rules covered 2.0
    # Let's check if the feedback generation for course C1_Full (id: course1["id"]) used the thresholds
    # If course total is 2.0, and rule is "<1.0: Needs review", ">=3.0: Good job!",
    # it implies current feedback logic might default if no rule matches exactly.
    # The survey_score_thresholds in this test are:
    # {"score_value": 1.0, "comparison": "lt", "feedback": "Course: Needs review"}, -> 2.0 is not < 1.0
    # {"score_value": 3.0, "comparison": "gte", "feedback": "Course: Good job!"}     -> 2.0 is not >= 3.0
    # So, it will likely get the default "Please review..."
    assert submit_result_data["course_feedback"][course1["id"]] == "Please review your performance for this course section."


    # 4. Student Views Own Results
    response_my_results = client.get(f"/api/v1/survey-attempts/{attempt_id}/results")
    assert response_my_results.status_code == HTTPStatus.OK, response_my_results.text
    my_results_data = response_my_results.json()
    assert my_results_data["id"] == attempt_id
    assert len(my_results_data["answers"]) == 2

    # 5. Teacher Views Student's Results
    client.post("/api/v1/users/login", json={"username": teacher_details["username"], "password": "testpassword"}) 
    response_teacher_view_results = client.get(f"/api/v1/survey-attempts/{attempt_id}/results")
    assert response_teacher_view_results.status_code == HTTPStatus.OK, response_teacher_view_results.text
    assert response_teacher_view_results.json()["id"] == attempt_id

    # 6. Teacher lists attempts for this survey
    response_list_attempts = client.get(f"/api/v1/survey-attempts/by-survey/{survey['id']}")
    assert response_list_attempts.status_code == HTTPStatus.OK
    list_attempts_data = response_list_attempts.json()
    assert isinstance(list_attempts_data, list)
    assert len(list_attempts_data) >= 1
    assert any(att["id"] == attempt_id for att in list_attempts_data)


def test_start_survey_unpublished_fail(
    client: TestClient,
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    _, teacher_details = authenticated_teacher_data_and_client
    client.post("/api/v1/users/login", json={"username": teacher_details["username"], "password": "testpassword"})
    course1 = create_course_for_attempt_test(client, "C_Unpub")
    survey_unpublished = create_survey_for_attempt_test(client, [course1["id"]], published=False, title_prefix="UnpublishedS")

    _, student_details = authenticated_student_data_and_client
    client.post("/api/v1/users/login", json={"username": student_details["username"], "password": "testpassword"})
    
    response_start = client.post("/api/v1/survey-attempts/start", json={"survey_id": survey_unpublished["id"]})
    assert response_start.status_code == HTTPStatus.NOT_FOUND 

def test_start_survey_non_existent_fail(authenticated_student_data_and_client: tuple[TestClient, dict]):
    client, _ = authenticated_student_data_and_client 
    non_existent_survey_id = str(ObjectId())
    response_start = client.post("/api/v1/survey-attempts/start", json={"survey_id": non_existent_survey_id})
    assert response_start.status_code == HTTPStatus.NOT_FOUND

def test_start_survey_already_active_returns_existing(
    client: TestClient,
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    _, teacher_details = authenticated_teacher_data_and_client
    client.post("/api/v1/users/login", json={"username": teacher_details["username"], "password": "testpassword"})
    course1 = create_course_for_attempt_test(client, "C_Active")
    survey = create_survey_for_attempt_test(client, [course1["id"]], published=True, title_prefix="ActiveS")

    _, student_details = authenticated_student_data_and_client
    client.post("/api/v1/users/login", json={"username": student_details["username"], "password": "testpassword"})
    
    response_start1 = client.post("/api/v1/survey-attempts/start", json={"survey_id": survey["id"]})
    assert response_start1.status_code == HTTPStatus.OK
    attempt_id1 = response_start1.json()["attempt_id"]

    response_start2 = client.post("/api/v1/survey-attempts/start", json={"survey_id": survey["id"]})
    assert response_start2.status_code == HTTPStatus.OK
    attempt_id2 = response_start2.json()["attempt_id"]
    assert attempt_id1 == attempt_id2 

def test_submit_answers_to_submitted_survey_fail(
    client: TestClient,
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    _, teacher_details = authenticated_teacher_data_and_client
    client.post("/api/v1/users/login", json={"username": teacher_details["username"], "password": "testpassword"})
    course1 = create_course_for_attempt_test(client, "C_SubFailAns")
    q1 = create_question_for_attempt_test(client, "Q_SubFailAns")
    create_qca_for_attempt_test(client, q1["id"], course1["id"])
    survey = create_survey_for_attempt_test(client, [course1["id"]])

    _, student_details = authenticated_student_data_and_client
    client.post("/api/v1/users/login", json={"username": student_details["username"], "password": "testpassword"})
    
    start_res = client.post("/api/v1/survey-attempts/start", json={"survey_id": survey["id"]})
    attempt_id = start_res.json()["attempt_id"]
    q_map = {q["question_id"]: q["qca_id"] for q in start_res.json()["questions"]}

    client.post(f"/api/v1/survey-attempts/{attempt_id}/answers", json={"answers": [{"qca_id": q_map[q1["id"]], "question_id": q1["id"], "answer_value": "a"}]})
    client.post(f"/api/v1/survey-attempts/{attempt_id}/submit") 

    response_answer_again = client.post(f"/api/v1/survey-attempts/{attempt_id}/answers", json={"answers": [{"qca_id": q_map[q1["id"]], "question_id": q1["id"], "answer_value": "b"}]})
    assert response_answer_again.status_code == HTTPStatus.BAD_REQUEST
    assert "already submitted" in response_answer_again.json()["detail"]

def test_submit_survey_already_submitted_fail(
    client: TestClient,
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    _, teacher_details = authenticated_teacher_data_and_client
    client.post("/api/v1/users/login", json={"username": teacher_details["username"], "password": "testpassword"})
    course1 = create_course_for_attempt_test(client, "C_SubFailSub")
    survey = create_survey_for_attempt_test(client, [course1["id"]])

    _, student_details = authenticated_student_data_and_client
    client.post("/api/v1/users/login", json={"username": student_details["username"], "password": "testpassword"})
    
    start_res = client.post("/api/v1/survey-attempts/start", json={"survey_id": survey["id"]})
    attempt_id = start_res.json()["attempt_id"]
    
    client.post(f"/api/v1/survey-attempts/{attempt_id}/submit") 
    response_submit_again = client.post(f"/api/v1/survey-attempts/{attempt_id}/submit") 
    assert response_submit_again.status_code == HTTPStatus.BAD_REQUEST
    assert "Survey has already been submitted" in response_submit_again.json()["detail"] # Corrected message

def test_list_my_survey_attempts(
    client: TestClient,
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    _, teacher_details = authenticated_teacher_data_and_client
    client.post("/api/v1/users/login", json={"username": teacher_details["username"], "password": "testpassword"})
    course1 = create_course_for_attempt_test(client, "C_MyList1")
    course2 = create_course_for_attempt_test(client, "C_MyList2")
    survey1 = create_survey_for_attempt_test(client, [course1["id"]], title_prefix="MyListS1")
    survey2 = create_survey_for_attempt_test(client, [course2["id"]], title_prefix="MyListS2")

    _, student_details = authenticated_student_data_and_client
    client.post("/api/v1/users/login", json={"username": student_details["username"], "password": "testpassword"})

    client.post("/api/v1/survey-attempts/start", json={"survey_id": survey1["id"]})
    start_res2 = client.post("/api/v1/survey-attempts/start", json={"survey_id": survey2["id"]})
    attempt2_id = start_res2.json()["attempt_id"]
    client.post(f"/api/v1/survey-attempts/{attempt2_id}/submit")

    response_my_attempts = client.get("/api/v1/survey-attempts/my")
    assert response_my_attempts.status_code == HTTPStatus.OK
    my_attempts_data = response_my_attempts.json()
    assert len(my_attempts_data) == 2
    survey_ids_in_response = {att["survey_id"] for att in my_attempts_data}
    assert survey1["id"] in survey_ids_in_response
    assert survey2["id"] in survey_ids_in_response

def test_get_results_unsubmitted_survey_fail(
    client: TestClient,
    authenticated_teacher_data_and_client: tuple[TestClient, dict],
    authenticated_student_data_and_client: tuple[TestClient, dict]
):
    _, teacher_details = authenticated_teacher_data_and_client
    client.post("/api/v1/users/login", json={"username": teacher_details["username"], "password": "testpassword"})
    course1 = create_course_for_attempt_test(client, "C_UnsubRes")
    survey = create_survey_for_attempt_test(client, [course1["id"]])

    _, student_details = authenticated_student_data_and_client
    client.post("/api/v1/users/login", json={"username": student_details["username"], "password": "testpassword"})
    
    start_res = client.post("/api/v1/survey-attempts/start", json={"survey_id": survey["id"]})
    attempt_id = start_res.json()["attempt_id"]

    response_results = client.get(f"/api/v1/survey-attempts/{attempt_id}/results")
    assert response_results.status_code == HTTPStatus.BAD_REQUEST
    assert "not yet available" in response_results.json()["detail"]

def test_get_results_not_owner_not_teacher_fail(
    client: TestClient,
    authenticated_teacher_data_and_client: tuple[TestClient, dict], 
    authenticated_student_data_and_client: tuple[TestClient, dict]  
):
    _, teacher1_details = authenticated_teacher_data_and_client
    client.post("/api/v1/users/login", json={"username": teacher1_details["username"], "password": "testpassword"})
    course1 = create_course_for_attempt_test(client, "C_AuthRes")
    survey = create_survey_for_attempt_test(client, [course1["id"]])

    _, student1_details = authenticated_student_data_and_client
    client.post("/api/v1/users/login", json={"username": student1_details["username"], "password": "testpassword"})
    start_res = client.post("/api/v1/survey-attempts/start", json={"survey_id": survey["id"]})
    attempt_id = start_res.json()["attempt_id"]
    client.post(f"/api/v1/survey-attempts/{attempt_id}/submit")

    student2_unique_suffix = uuid.uuid4().hex[:8]
    student2_signup_data = {"username": f"student2_auth_{student2_unique_suffix}@example.com", "display_name": "Student Two Auth", "role": "student", "password": "testpassword"}
    client.post("/api/v1/users/signup", json=student2_signup_data) 
    client.post("/api/v1/users/login", json={"username": student2_signup_data["username"], "password": "testpassword"}) 

    response_s2_view_s1_results = client.get(f"/api/v1/survey-attempts/{attempt_id}/results")
    assert response_s2_view_s1_results.status_code == HTTPStatus.FORBIDDEN
    assert "Not authorized" in response_s2_view_s1_results.json()["detail"]
