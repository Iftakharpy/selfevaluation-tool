# api/app/survey_attempts/router.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict, Any, Tuple 
from bson import ObjectId
from datetime import datetime, UTC 

from app.core.db import (
    get_survey_collection, 
    get_survey_attempt_collection, 
    get_student_answer_collection,
    get_question_collection,
    get_qca_collection,
    get_user_collection
)
from app.users.auth import get_current_active_user, require_teacher_role 
from app.users.data_types import UserInDB, PyObjectId, RoleEnum
from app.surveys.data_types import ( # These come from surveys.data_types
    SurveyInDB, 
    ScoreFeedbackItem as SurveyScoreFeedbackItem, # Alias for clarity if needed
    OutcomeThresholdItem, 
    OutcomeCategoryEnum  
)
from app.surveys.router import _get_survey_question_details # Helper from survey router
from app.questions.data_types import ScoreFeedbackItem as QuestionScoreFeedbackItem, FeedbackComparisonEnum, AnswerTypeEnum 
from app.qca.data_types import AnswerAssociationTypeEnum
from .data_types import (
    SurveyAttemptCreateRequest, SurveyAttemptStartOut, SurveyAttemptOut, 
    StudentAnswerPayload, StudentAnswerInDB, StudentAnswerOut,
    SubmitAnswersRequest, SurveyAttemptInDB, SurveyAttemptResultOut
)
from app.core.settings import STANDARD_QUESTION_MAX_SCORE # IMPORTED CONSTANT

SurveyAttemptRouter = APIRouter()


def _prepare_student_answer_dict_for_out(answer_dict_from_db: dict) -> dict:
    if "_id" in answer_dict_from_db:
        answer_dict_from_db["id"] = str(answer_dict_from_db.pop("_id"))
    for field in ["qca_id", "question_id", "survey_attempt_id", "student_id"]:
        if field in answer_dict_from_db and isinstance(answer_dict_from_db[field], ObjectId):
            answer_dict_from_db[field] = str(answer_dict_from_db[field])
    return answer_dict_from_db

def _prepare_survey_attempt_dict_for_out(attempt_dict_from_db: dict) -> dict:
    if "_id" in attempt_dict_from_db:
        attempt_dict_from_db["id"] = str(attempt_dict_from_db.pop("_id"))
    for field in ["student_id", "survey_id"]:
        if field in attempt_dict_from_db and isinstance(attempt_dict_from_db[field], ObjectId):
            attempt_dict_from_db[field] = str(attempt_dict_from_db[field])
    
    if "course_outcome_categorization" not in attempt_dict_from_db or attempt_dict_from_db.get("course_outcome_categorization") is None:
        attempt_dict_from_db["course_outcome_categorization"] = {}
    if "max_scores_per_course" not in attempt_dict_from_db or attempt_dict_from_db.get("max_scores_per_course") is None:
        attempt_dict_from_db["max_scores_per_course"] = {}
    if "max_overall_survey_score" not in attempt_dict_from_db: 
         attempt_dict_from_db["max_overall_survey_score"] = None
    if "student_display_name" not in attempt_dict_from_db:
        attempt_dict_from_db["student_display_name"] = None

    return attempt_dict_from_db

async def calculate_score_for_answer(question_dict: Dict, student_answer_value: Any) -> float:
    q_type_str = question_dict.get("answer_type")
    rules = question_dict.get("scoring_rules", {})
    options = question_dict.get("answer_options", {})
    raw_score = 0.0

    if student_answer_value is None: 
        raw_score = float(rules.get("score_if_unanswered", 0.0))
        return max(0.0, min(raw_score, STANDARD_QUESTION_MAX_SCORE))

    try:
        q_type = AnswerTypeEnum(q_type_str)
    except ValueError:
        return 0.0

    if q_type == AnswerTypeEnum.multiple_choice:
        correct_key = rules.get("correct_option_key")
        option_scores = rules.get("option_scores")
        if option_scores and isinstance(option_scores, dict) and student_answer_value in option_scores:
            raw_score = float(option_scores[student_answer_value])
        elif correct_key is not None:
            raw_score = STANDARD_QUESTION_MAX_SCORE if correct_key == student_answer_value else 0.0
    
    elif q_type == AnswerTypeEnum.multiple_select:
        if not isinstance(student_answer_value, list): return 0.0
        option_scores = rules.get("option_scores")
        correct_option_keys = set(rules.get("correct_option_keys", []))
        selected_keys = set(student_answer_value)
        current_raw_score = 0.0
        if option_scores and isinstance(option_scores, dict):
            for sel_key in selected_keys:
                if sel_key in option_scores:
                    current_raw_score += float(option_scores[sel_key])
        elif correct_option_keys:
            num_correct_defined = len(correct_option_keys)
            score_val = float(rules.get("score_per_correct", STANDARD_QUESTION_MAX_SCORE / num_correct_defined if num_correct_defined > 0 else 0.0))
            penalty_val = float(rules.get("penalty_per_incorrect", 0.0))
            for key in selected_keys:
                if key in correct_option_keys: current_raw_score += score_val
                elif key in options: current_raw_score += penalty_val
        raw_score = current_raw_score
    
    elif q_type == AnswerTypeEnum.input:
        expected_answers = rules.get("expected_answers", [])
        raw_score = float(rules.get("default_incorrect_score", 0.0))
        if isinstance(student_answer_value, str):
            for expected in expected_answers:
                expected_text = expected.get("text", "")
                case_sensitive = expected.get("case_sensitive", False)
                match_score = float(expected.get("score", 0.0))
                is_match = (student_answer_value == expected_text) if case_sensitive else (student_answer_value.lower() == expected_text.lower())
                if is_match:
                    raw_score = match_score; break 
    
    elif q_type == AnswerTypeEnum.range:
        try:
            val = float(student_answer_value)
            min_opt_val = float(options.get("min", 0)); max_opt_val = float(options.get("max", 10))
            target_val = float(rules.get("target_value", (min_opt_val + max_opt_val) / 2 ))
            score_at_target = float(rules.get("score_at_target", STANDARD_QUESTION_MAX_SCORE)) 
            score_per_dev_unit = float(rules.get("score_per_deviation_unit", -1.0))
            deviation = abs(val - target_val)
            raw_score = score_at_target + (deviation * score_per_dev_unit)
        except (ValueError, TypeError): raw_score = 0.0
            
    final_score = max(0.0, min(raw_score, STANDARD_QUESTION_MAX_SCORE))
    return round(final_score, 2)

def _evaluate_feedback_rules(
    score: float, 
    feedback_rules_input: Optional[List[Any]] # Accept list of dicts or model instances
) -> Optional[str]:
    if not feedback_rules_input: return None
    # Using Any for rule_input as it can be dict or Pydantic model before validation
    feedback_rules_validated: List[Union[QuestionScoreFeedbackItem, SurveyScoreFeedbackItem]] = []
    for rule_input_untyped in feedback_rules_input:
        rule_input: Any = rule_input_untyped # type hint for clarity
        if isinstance(rule_input, (QuestionScoreFeedbackItem, SurveyScoreFeedbackItem)):
            feedback_rules_validated.append(rule_input)
        elif isinstance(rule_input, dict):
            try: 
                feedback_rules_validated.append(QuestionScoreFeedbackItem.model_validate(rule_input))
            except Exception:
                try: 
                    feedback_rules_validated.append(SurveyScoreFeedbackItem.model_validate(rule_input))
                except Exception: continue
        else: continue
            
    for rule in feedback_rules_validated: 
        match = False
        rule_score_value = float(rule.score_value)
        if rule.comparison == FeedbackComparisonEnum.lt: match = score < rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.lte: match = score <= rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.gt: match = score > rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.gte: match = score >= rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.eq: match = score == rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.neq: match = score != rule_score_value
        if match: return rule.feedback
    return None

def _evaluate_outcome_rules(
    score: float,
    outcome_rules_input: Optional[List[Any]] # Accept list of dicts or model instances
) -> OutcomeCategoryEnum:
    if not outcome_rules_input: return OutcomeCategoryEnum.UNDEFINED
    outcome_rules_validated: List[OutcomeThresholdItem] = []
    for rule_input_untyped in outcome_rules_input:
        rule_input: Any = rule_input_untyped
        if isinstance(rule_input, OutcomeThresholdItem):
            outcome_rules_validated.append(rule_input)
        elif isinstance(rule_input, dict):
            try: outcome_rules_validated.append(OutcomeThresholdItem.model_validate(rule_input))
            except Exception: continue
        else: continue
    outcome_rules_validated.sort(key=lambda r: (r.score_value, r.comparison.value))
    for rule in outcome_rules_validated:
        match = False
        rule_score_value = float(rule.score_value)
        if rule.comparison == FeedbackComparisonEnum.lt: match = score < rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.lte: match = score <= rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.gt: match = score > rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.gte: match = score >= rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.eq: match = score == rule_score_value
        elif rule.comparison == FeedbackComparisonEnum.neq: match = score != rule_score_value
        if match: return rule.outcome
    return OutcomeCategoryEnum.UNDEFINED

async def generate_all_feedback_and_outcomes_for_attempt(
    attempt_dict: Dict, survey_obj: SurveyInDB, student_answers_list_with_scores: List[Dict],
    qca_collection, question_collection
) -> Tuple[Dict[str, str], Dict[str, List[str]], Optional[str], Dict[str, OutcomeCategoryEnum]]:
    course_scores = attempt_dict.get("course_scores", {}) 
    final_overall_course_feedback: Dict[str, str] = {} 
    detailed_feedback_per_course: Dict[str, List[str]] = {str(cid_obj): [] for cid_obj in survey_obj.course_ids}
    final_course_outcome_categories: Dict[str, OutcomeCategoryEnum] = {}

    for ans_with_score_dict in student_answers_list_with_scores:
        qca = await qca_collection.find_one({"_id": ans_with_score_dict["qca_id"]})
        question = await question_collection.find_one({"_id": ans_with_score_dict["question_id"]})
        if not qca or not question: continue
        ans_score = ans_with_score_dict.get("score_achieved", 0.0)
        course_id_str = str(qca["course_id"]) 
        if course_id_str not in detailed_feedback_per_course: 
            detailed_feedback_per_course[course_id_str] = []
        feedback_msg = _evaluate_feedback_rules(ans_score, qca.get("feedbacks_based_on_score")) or \
                       _evaluate_feedback_rules(ans_score, question.get("default_feedbacks_on_score"))
        if feedback_msg:
            detailed_feedback_per_course[course_id_str].append(f"Q: {question['title']}: {feedback_msg}")

    for course_id_pyobj in survey_obj.course_ids:
        course_id_str = str(course_id_pyobj)
        total_score_for_course = course_scores.get(course_id_str, 0.0)
        
        course_feedback_rules_list = (survey_obj.course_skill_total_score_thresholds or {}).get(course_id_str)
        if course_feedback_rules_list:
            overall_fb_for_course = _evaluate_feedback_rules(total_score_for_course, course_feedback_rules_list)
            if overall_fb_for_course:
                final_overall_course_feedback[course_id_str] = overall_fb_for_course
        if course_id_str not in final_overall_course_feedback:
             final_overall_course_feedback[course_id_str] = "Please review your performance for this course section."

        course_outcome_rules_list = (survey_obj.course_outcome_thresholds or {}).get(course_id_str)
        category = _evaluate_outcome_rules(total_score_for_course, course_outcome_rules_list)
        final_course_outcome_categories[course_id_str] = category

    overall_survey_feedback_str = "Thank you for completing the survey. Your results are summarized above." 
    return final_overall_course_feedback, detailed_feedback_per_course, overall_survey_feedback_str, final_course_outcome_categories

async def _populate_attempt_response_data(attempt_dict: dict, survey_collection, user_collection) -> None:
    """Populates max scores and student display name into the attempt dictionary."""
    survey_doc = await survey_collection.find_one({"_id": attempt_dict["survey_id"]})
    if survey_doc:
        attempt_dict["max_scores_per_course"] = survey_doc.get("max_scores_per_course", {})
        attempt_dict["max_overall_survey_score"] = survey_doc.get("max_overall_survey_score")
    else:
        attempt_dict["max_scores_per_course"] = {}
        attempt_dict["max_overall_survey_score"] = None
    
    if "student_id" in attempt_dict:
        student_doc = await user_collection.find_one({"_id": attempt_dict["student_id"]})
        attempt_dict["student_display_name"] = student_doc.get("display_name") if student_doc else "Unknown Student"

# Routes start here
@SurveyAttemptRouter.post("/start", response_model=SurveyAttemptStartOut)
async def start_survey_attempt(
    attempt_create: SurveyAttemptCreateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    survey_collection = get_survey_collection()
    attempt_collection = get_survey_attempt_collection()
    survey_doc = await survey_collection.find_one({"_id": attempt_create.survey_id, "is_published": True})
    if not survey_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published survey not found or does not exist.")
    survey = SurveyInDB.model_validate(survey_doc) 
    existing_attempt = await attempt_collection.find_one({"student_id": current_user.id, "survey_id": survey.id, "is_submitted": False})
    if existing_attempt:
        questions = await _get_survey_question_details(survey)
        return SurveyAttemptStartOut(attempt_id=str(existing_attempt["_id"]), survey_id=str(survey.id), student_id=str(current_user.id), started_at=existing_attempt["started_at"], questions=questions)
    new_attempt_data = {"student_id": current_user.id, "survey_id": survey.id}
    new_attempt_obj = SurveyAttemptInDB(**new_attempt_data)
    result = await attempt_collection.insert_one(new_attempt_obj.model_dump(by_alias=True))
    created_attempt = await attempt_collection.find_one({"_id": result.inserted_id})
    if not created_attempt: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not start survey attempt.")
    questions = await _get_survey_question_details(survey)
    return SurveyAttemptStartOut(attempt_id=str(created_attempt["_id"]), survey_id=str(survey.id), student_id=str(current_user.id), started_at=created_attempt["started_at"], questions=questions)

@SurveyAttemptRouter.post("/{attempt_id}/answers", response_model=List[StudentAnswerOut])
async def submit_answers_for_attempt(
    attempt_id: str, answers_request: SubmitAnswersRequest, current_user: UserInDB = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(attempt_id): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attempt ID format.")
    attempt_collection = get_survey_attempt_collection()
    answer_collection = get_student_answer_collection()
    qca_collection = get_qca_collection()
    question_collection_ref = get_question_collection()
    attempt_obj_id = PyObjectId(attempt_id)
    attempt = await attempt_collection.find_one({"_id": attempt_obj_id, "student_id": current_user.id})
    if not attempt: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey attempt not found or not yours.")
    if attempt["is_submitted"]: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey already submitted, cannot change answers.")
    processed_answers_out = []
    for ans_payload in answers_request.answers:
        qca = await qca_collection.find_one({"_id": ans_payload.qca_id})
        question_from_db = await question_collection_ref.find_one({"_id": ans_payload.question_id})
        if not qca or not question_from_db or qca["question_id"] != ans_payload.question_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid QCA/Question ID for payload: {ans_payload.qca_id}/{ans_payload.question_id}.")
        try:
            q_type = AnswerTypeEnum(question_from_db["answer_type"])
            q_options = question_from_db.get("answer_options", {})
            answer_val = ans_payload.answer_value
            if q_type == AnswerTypeEnum.multiple_choice and not (isinstance(answer_val, str) and q_options and answer_val in q_options): raise ValueError(f"Invalid option '{answer_val}'.")
            elif q_type == AnswerTypeEnum.multiple_select:
                if not isinstance(answer_val, list): raise ValueError("Answer must be a list.")
                if q_options:
                    for item in answer_val:
                        if not (isinstance(item, str) and item in q_options): raise ValueError(f"Invalid option '{item}'.")
            elif q_type == AnswerTypeEnum.input and not isinstance(answer_val, str): raise ValueError("Answer must be a string.")
            elif q_type == AnswerTypeEnum.range:
                if not isinstance(answer_val, (int, float)): raise ValueError("Answer must be a number.")
                if q_options:
                    min_v, max_v = q_options.get("min"), q_options.get("max")
                    if min_v is not None and answer_val < min_v: raise ValueError(f"Value below min {min_v}.")
                    if max_v is not None and answer_val > max_v: raise ValueError(f"Value above max {max_v}.")
        except ValueError as ve: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Q '{question_from_db['title']}': {ve}")
        
        db_data = ans_payload.model_dump()
        db_data.update({"survey_attempt_id": attempt_obj_id, "student_id": current_user.id, "answered_at": datetime.now(UTC), "score_achieved": None})
        await answer_collection.replace_one({"survey_attempt_id": attempt_obj_id, "qca_id": ans_payload.qca_id, "student_id": current_user.id}, db_data, upsert=True)
        stored = await answer_collection.find_one({"survey_attempt_id": attempt_obj_id, "qca_id": ans_payload.qca_id, "student_id": current_user.id})
        if stored: processed_answers_out.append(StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(stored.copy())))
    return processed_answers_out

@SurveyAttemptRouter.post("/{attempt_id}/submit", response_model=SurveyAttemptResultOut)
async def submit_survey_attempt(
    attempt_id: str, current_user: UserInDB = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(attempt_id): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attempt ID format.")
    attempt_collection = get_survey_attempt_collection(); answer_collection = get_student_answer_collection()
    survey_collection = get_survey_collection(); qca_collection = get_qca_collection()
    question_collection = get_question_collection(); user_collection = get_user_collection()
    attempt_obj_id = PyObjectId(attempt_id)
    attempt_dict = await attempt_collection.find_one({"_id": attempt_obj_id, "student_id": current_user.id})
    if not attempt_dict: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey attempt not found or not yours.")
    if attempt_dict["is_submitted"]: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey has already been submitted.")
    survey_doc = await survey_collection.find_one({"_id": attempt_dict["survey_id"]})
    if not survey_doc: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated survey not found.")    
    survey_obj = SurveyInDB.model_validate(survey_doc)
    answers_cursor = answer_collection.find({"survey_attempt_id": attempt_obj_id})
    answers_with_scores: List[Dict[str,Any]] = []
    calculated_course_scores: Dict[str, float] = {str(cid): 0.0 for cid in survey_obj.course_ids}
    async for ans_raw in answers_cursor:
        ans = ans_raw.copy()
        qca = await qca_collection.find_one({"_id": ans["qca_id"]})
        q_doc = await question_collection.find_one({"_id": qca["question_id"]}) if qca else None
        if not qca or not q_doc: continue
        score = await calculate_score_for_answer(q_doc, ans["answer_value"])
        await answer_collection.update_one({"_id": ans["_id"]}, {"$set": {"score_achieved": score}})
        ans["score_achieved"] = score; answers_with_scores.append(ans)
        course_id_str = str(qca["course_id"])
        score_contrib = score * -1 if qca.get("answer_association_type") == AnswerAssociationTypeEnum.negative.value else score
        if course_id_str in calculated_course_scores: calculated_course_scores[course_id_str] += score_contrib
    
    attempt_for_feedback = attempt_dict.copy(); attempt_for_feedback["course_scores"] = calculated_course_scores
    course_fb, detailed_fb, overall_fb, outcomes = await generate_all_feedback_and_outcomes_for_attempt(attempt_for_feedback, survey_obj, answers_with_scores, qca_collection, question_collection)
    update_payload = {"is_submitted": True, "submitted_at": datetime.now(UTC), "course_scores": calculated_course_scores, "course_feedback": course_fb, "detailed_feedback": detailed_fb, "overall_survey_feedback": overall_fb, "course_outcome_categorization": outcomes}
    await attempt_collection.update_one({"_id": attempt_obj_id}, {"$set": update_payload})
    updated_attempt = await attempt_collection.find_one({"_id": attempt_obj_id})
    if not updated_attempt: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve attempt post-submission.")
    await _populate_attempt_response_data(updated_attempt, survey_collection, user_collection)
    result_out = SurveyAttemptResultOut.model_validate(_prepare_survey_attempt_dict_for_out(updated_attempt.copy()))
    result_out.answers = [StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(a.copy())) for a in answers_with_scores]
    return result_out

@SurveyAttemptRouter.get("/{attempt_id}/results", response_model=SurveyAttemptResultOut)
async def get_survey_attempt_results(
    attempt_id: str, current_user: UserInDB = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(attempt_id): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attempt ID format.")
    attempt_collection = get_survey_attempt_collection(); answer_collection = get_student_answer_collection()
    survey_collection = get_survey_collection(); user_collection = get_user_collection()
    attempt_dict_raw = await attempt_collection.find_one({"_id": PyObjectId(attempt_id)})
    if not attempt_dict_raw: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey attempt not found.")
    attempt_dict = attempt_dict_raw.copy()
    is_owner = attempt_dict["student_id"] == current_user.id
    is_teacher_auth = False
    if current_user.role == RoleEnum.teacher:
        survey = await survey_collection.find_one({"_id": attempt_dict["survey_id"]})
        if survey and survey["created_by"] == current_user.id: is_teacher_auth = True
    if not (is_owner or is_teacher_auth): raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these results.")
    if not attempt_dict["is_submitted"]: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey results are not yet available (not submitted).")
    await _populate_attempt_response_data(attempt_dict, survey_collection, user_collection)
    answers_list = await answer_collection.find({"survey_attempt_id": PyObjectId(attempt_id)}).to_list(length=None)
    result_out = SurveyAttemptResultOut.model_validate(_prepare_survey_attempt_dict_for_out(attempt_dict))
    result_out.answers = [StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(a.copy())) for a in answers_list]
    return result_out

@SurveyAttemptRouter.get("/my", response_model=List[SurveyAttemptOut])
async def list_my_survey_attempts(
    current_user: UserInDB = Depends(get_current_active_user), skip: int = 0, limit: int = 20, include_answers: bool = Query(False)
):
    attempt_coll = get_survey_attempt_collection(); ans_coll = get_student_answer_collection()
    survey_coll_ref = get_survey_collection(); user_coll_ref = get_user_collection()
    attempts_cursor = attempt_coll.find({"student_id": current_user.id}).skip(skip).limit(limit).sort("started_at", -1)
    attempts_list_raw = await attempts_cursor.to_list(length=limit)
    output_list = []
    for attempt_raw in attempts_list_raw:
        attempt_db = attempt_raw.copy()
        await _populate_attempt_response_data(attempt_db, survey_coll_ref, user_coll_ref)
        attempt_out = SurveyAttemptOut.model_validate(_prepare_survey_attempt_dict_for_out(attempt_db))
        if include_answers and attempt_out.is_submitted:
            answers_raw = await ans_coll.find({"survey_attempt_id": PyObjectId(attempt_out.id)}).to_list(length=None)
            attempt_out.answers = [StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(a.copy())) for a in answers_raw]
        output_list.append(attempt_out)
    return output_list

@SurveyAttemptRouter.get("/by-survey/{survey_id}", response_model=List[SurveyAttemptOut])
async def list_attempts_for_survey(
    survey_id: str, current_user: UserInDB = Depends(require_teacher_role), skip: int = 0, limit: int = 50, include_answers: bool = Query(False)
):
    if not ObjectId.is_valid(survey_id): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid survey ID.")
    survey_coll = get_survey_collection(); attempt_coll = get_survey_attempt_collection()
    ans_coll = get_student_answer_collection(); user_coll_ref = get_user_collection()
    survey_obj_id = PyObjectId(survey_id)
    survey_doc = await survey_coll.find_one({"_id": survey_obj_id})
    if not survey_doc: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found.")
    if survey_doc["created_by"] != current_user.id: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
    
    attempts_cursor = attempt_coll.find({"survey_id": survey_obj_id, "is_submitted": True}).skip(skip).limit(limit).sort("submitted_at", -1)
    attempts_list_raw = await attempts_cursor.to_list(length=limit)
    output_list = []
    for attempt_raw in attempts_list_raw:
        attempt_db = attempt_raw.copy()
        attempt_db["max_scores_per_course"] = survey_doc.get("max_scores_per_course", {})
        attempt_db["max_overall_survey_score"] = survey_doc.get("max_overall_survey_score")
        if "student_id" in attempt_db:
            student = await user_coll_ref.find_one({"_id": attempt_db["student_id"]})
            attempt_db["student_display_name"] = student.get("display_name") if student else "Unknown"
        
        attempt_out = SurveyAttemptOut.model_validate(_prepare_survey_attempt_dict_for_out(attempt_db))
        if include_answers:
            answers_raw = await ans_coll.find({"survey_attempt_id": PyObjectId(attempt_out.id)}).to_list(length=None)
            attempt_out.answers = [StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(a.copy())) for a in answers_raw]
        output_list.append(attempt_out)
    return output_list