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
    get_course_collection
)
from app.users.auth import get_current_active_user, require_teacher_role 
from app.users.data_types import UserInDB, PyObjectId, RoleEnum
from app.surveys.data_types import (
    SurveyInDB, 
    ScoreFeedbackItem as SurveyScoreFeedbackItem,
    OutcomeThresholdItem, # MODIFIED: Import OutcomeThresholdItem
    OutcomeCategoryEnum   # MODIFIED: Import OutcomeCategoryEnum
)
from app.surveys.router import _get_survey_question_details 
from app.questions.data_types import ScoreFeedbackItem as QuestionScoreFeedbackItem, FeedbackComparisonEnum, AnswerTypeEnum 
from app.qca.data_types import AnswerAssociationTypeEnum # MODIFIED: Import AnswerAssociationTypeEnum
from .data_types import (
    SurveyAttemptCreateRequest, SurveyAttemptStartOut, SurveyAttemptOut, 
    StudentAnswerPayload, StudentAnswerInDB, StudentAnswerOut,
    SubmitAnswersRequest, SurveyAttemptInDB, SurveyAttemptResultOut
)

SurveyAttemptRouter = APIRouter()

# --- Helper functions to prepare DB dicts for Pydantic Out models ---
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
    # MODIFIED: Ensure course_outcome_categorization is present if it's empty, for model validation
    if "course_outcome_categorization" not in attempt_dict_from_db:
        attempt_dict_from_db["course_outcome_categorization"] = {}
    return attempt_dict_from_db


# --- Enhanced Scoring Function ---
async def calculate_score_for_answer(question_dict: Dict, student_answer_value: Any) -> float:
    q_type_str = question_dict.get("answer_type")
    rules = question_dict.get("scoring_rules", {})
    options = question_dict.get("answer_options", {})

    if student_answer_value is None:
        return float(rules.get("score_if_unanswered", 0.0))
    score = 0.0
    try:
        q_type = AnswerTypeEnum(q_type_str)
    except ValueError:
        print(f"Warning: Invalid answer_type '{q_type_str}' for question ID {question_dict.get('_id')}")
        return 0.0

    if q_type == AnswerTypeEnum.multiple_choice:
        correct_key = rules.get("correct_option_key")
        option_scores = rules.get("option_scores")
        if option_scores and isinstance(option_scores, dict) and student_answer_value in option_scores:
            score = float(option_scores[student_answer_value])
        elif correct_key is not None:
            score = float(rules.get("score_if_correct", 1.0)) if correct_key == student_answer_value else float(rules.get("score_if_incorrect", 0.0))
        else: score = float(rules.get("default_score_for_choice", 0.0))

    elif q_type == AnswerTypeEnum.multiple_select:
        if not isinstance(student_answer_value, list): return 0.0
        correct_keys = set(rules.get("correct_option_keys", []))
        option_scores = rules.get("option_scores")
        score_per_correct = float(rules.get("score_per_correct", 1.0))
        penalty_per_incorrect = float(rules.get("penalty_per_incorrect", 0.0)) 
        selected_keys = set(student_answer_value)
        if option_scores and isinstance(option_scores, dict):
            for sel_key in selected_keys:
                if sel_key in option_scores: score += float(option_scores[sel_key])
        else:
            for key in selected_keys:
                if key in correct_keys: score += score_per_correct
                elif key in options: score += penalty_per_incorrect 
        # score = max(0, score) # Optional

    elif q_type == AnswerTypeEnum.input:
        expected_answers = rules.get("expected_answers", [])
        default_score = float(rules.get("default_incorrect_score", 0.0))
        score = default_score 
        if isinstance(student_answer_value, str): 
            for expected in expected_answers: 
                expected_text = expected.get("text", "")
                case_sensitive = expected.get("case_sensitive", False)
                match = (student_answer_value == expected_text) if case_sensitive else (student_answer_value.lower() == expected_text.lower())
                if match:
                    score = float(expected.get("score", default_score)) 
                    break 
    
    elif q_type == AnswerTypeEnum.range:
        try:
            val = float(student_answer_value)
            target = float(rules.get("target_value", 0.0))
            score_at_target = float(rules.get("score_at_target", 0.0))
            score_per_dev = float(rules.get("score_per_deviation_unit", 0.0)) 
            score = score_at_target + (abs(val - target) * score_per_dev)
        except (ValueError, TypeError): score = 0.0
    return score

# --- Enhanced Feedback and Outcome Generation Functions ---
def _evaluate_feedback_rules(
    score: float, 
    feedback_rules_input: Optional[List[QuestionScoreFeedbackItem | SurveyScoreFeedbackItem | Dict]]
) -> Optional[str]:
    if not feedback_rules_input: return None
    
    feedback_rules_validated: List[QuestionScoreFeedbackItem | SurveyScoreFeedbackItem] = []
    for rule_input in feedback_rules_input:
        if isinstance(rule_input, (QuestionScoreFeedbackItem, SurveyScoreFeedbackItem)):
            feedback_rules_validated.append(rule_input)
        elif isinstance(rule_input, dict):
            try:
                feedback_rules_validated.append(QuestionScoreFeedbackItem.model_validate(rule_input))
            except Exception as e:
                print(f"Warning: Could not parse feedback rule dict: {rule_input}, error: {e}")
                continue
        else:
            print(f"Warning: Invalid type for feedback rule: {type(rule_input)}")
            continue

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

# MODIFIED: New helper for outcome categorization
def _evaluate_outcome_rules(
    score: float,
    outcome_rules_input: Optional[List[OutcomeThresholdItem | Dict]]
) -> OutcomeCategoryEnum:
    if not outcome_rules_input: return OutcomeCategoryEnum.UNDEFINED

    outcome_rules_validated: List[OutcomeThresholdItem] = []
    for rule_input in outcome_rules_input:
        if isinstance(rule_input, OutcomeThresholdItem):
            outcome_rules_validated.append(rule_input)
        elif isinstance(rule_input, dict):
            try:
                outcome_rules_validated.append(OutcomeThresholdItem.model_validate(rule_input))
            except Exception as e:
                print(f"Warning: Could not parse outcome rule dict: {rule_input}, error: {e}")
                continue
        else:
             print(f"Warning: Invalid type for outcome rule: {type(rule_input)}")
             continue
    
    # Sort rules: typically, you'd want to evaluate in a specific order,
    # e.g., more specific (lower 'lt' values) before broader ones, or based on score_value.
    # For simplicity, we'll take the first match based on list order.
    # A more robust system might sort by score_value and comparison type.
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


async def generate_all_feedback_and_outcomes_for_attempt( # MODIFIED: Renamed and updated return type
    attempt_dict: Dict, survey_obj: SurveyInDB, student_answers_list_with_scores: List[Dict],
    qca_collection, question_collection
) -> Tuple[Dict[str, str], Dict[str, List[str]], Optional[str], Dict[str, OutcomeCategoryEnum]]: # MODIFIED: Added outcome dict to tuple
    
    course_scores = attempt_dict.get("course_scores", {}) 
    final_overall_course_feedback: Dict[str, str] = {} 
    detailed_feedback_per_course: Dict[str, List[str]] = {str(cid): [] for cid in course_scores.keys()}
    final_course_outcome_categories: Dict[str, OutcomeCategoryEnum] = {} # MODIFIED: New dict for outcomes

    for ans_with_score_dict in student_answers_list_with_scores:
        qca = await qca_collection.find_one({"_id": ans_with_score_dict["qca_id"]})
        question = await question_collection.find_one({"_id": ans_with_score_dict["question_id"]})
        if not qca or not question: continue

        ans_score = ans_with_score_dict.get("score_achieved", 0.0)
        course_id_str = str(qca["course_id"]) 
        
        feedback_msg = _evaluate_feedback_rules(ans_score, qca.get("feedbacks_based_on_score")) or \
                       _evaluate_feedback_rules(ans_score, question.get("default_feedbacks_on_score"))
        
        if feedback_msg:
            if course_id_str not in detailed_feedback_per_course:
                 detailed_feedback_per_course[course_id_str] = []
            detailed_feedback_per_course[course_id_str].append(f"Q: {question['title']}: {feedback_msg}")

    if survey_obj.course_skill_total_score_thresholds or survey_obj.course_outcome_thresholds:
        for course_id_str, total_score_for_course in course_scores.items():
            # Feedback
            course_feedback_rules = survey_obj.course_skill_total_score_thresholds.get(course_id_str)
            if course_feedback_rules:
                overall_fb_for_course = _evaluate_feedback_rules(total_score_for_course, course_feedback_rules)
                if overall_fb_for_course:
                    final_overall_course_feedback[course_id_str] = overall_fb_for_course
            if course_id_str not in final_overall_course_feedback:
                 final_overall_course_feedback[course_id_str] = "Please review your performance for this course section."

            # Outcome Categorization (MODIFIED)
            course_outcome_rules = survey_obj.course_outcome_thresholds.get(course_id_str) # Fetch from PyObjectId keys if stored that way
            category = _evaluate_outcome_rules(total_score_for_course, course_outcome_rules)
            final_course_outcome_categories[course_id_str] = category


    overall_survey_feedback_str = "Thank you for completing the survey. Your results are summarized above." 
    
    return final_overall_course_feedback, detailed_feedback_per_course, overall_survey_feedback_str, final_course_outcome_categories # MODIFIED: Return outcomes


@SurveyAttemptRouter.post("/start", response_model=SurveyAttemptStartOut)
async def start_survey_attempt(
    attempt_create: SurveyAttemptCreateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    survey_collection = get_survey_collection()
    attempt_collection = get_survey_attempt_collection()

    survey_dict = await survey_collection.find_one({"_id": attempt_create.survey_id, "is_published": True})
    if not survey_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published survey not found.")
    survey = SurveyInDB.model_validate(survey_dict) 

    existing_attempt_dict = await attempt_collection.find_one({
        "student_id": current_user.id,
        "survey_id": survey.id,
        "is_submitted": False
    })

    if existing_attempt_dict:
        questions = await _get_survey_question_details(survey)
        return SurveyAttemptStartOut(
            attempt_id=str(existing_attempt_dict["_id"]),
            survey_id=str(survey.id),
            student_id=str(current_user.id),
            started_at=existing_attempt_dict["started_at"],
            questions=questions
        )

    new_attempt_obj = SurveyAttemptInDB(student_id=current_user.id, survey_id=survey.id)
    result = await attempt_collection.insert_one(new_attempt_obj.model_dump(by_alias=True))
    created_attempt_dict = await attempt_collection.find_one({"_id": result.inserted_id})
    if not created_attempt_dict:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not start survey attempt.")

    questions = await _get_survey_question_details(survey)
    return SurveyAttemptStartOut(
        attempt_id=str(created_attempt_dict["_id"]),
        survey_id=str(survey.id),
        student_id=str(current_user.id),
        started_at=created_attempt_dict["started_at"],
        questions=questions
    )

@SurveyAttemptRouter.post("/{attempt_id}/answers", response_model=List[StudentAnswerOut])
async def submit_answers_for_attempt(
    attempt_id: str,
    answers_request: SubmitAnswersRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(attempt_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attempt ID format.")
    
    attempt_collection = get_survey_attempt_collection()
    answer_collection = get_student_answer_collection()
    qca_collection = get_qca_collection()
    question_collection_ref = get_question_collection()

    attempt_obj_id = PyObjectId(attempt_id)
    attempt = await attempt_collection.find_one({"_id": attempt_obj_id, "student_id": current_user.id})
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey attempt not found or not yours.")
    if attempt["is_submitted"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey already submitted, cannot change answers.")

    processed_answers_out = []
    for ans_payload in answers_request.answers:
        qca = await qca_collection.find_one({"_id": ans_payload.qca_id})
        question_from_db = await question_collection_ref.find_one({"_id": ans_payload.question_id})

        if not qca or not question_from_db or qca["question_id"] != ans_payload.question_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Invalid QCA ID {ans_payload.qca_id} or Question ID {ans_payload.question_id}.")
        
        try:
            q_type = AnswerTypeEnum(question_from_db["answer_type"])
            q_options = question_from_db.get("answer_options", {})
            answer_val = ans_payload.answer_value

            if q_type == AnswerTypeEnum.multiple_choice:
                if not (isinstance(answer_val, str) and q_options and answer_val in q_options):
                    raise ValueError(f"Invalid option '{answer_val}' for multiple choice.")
            elif q_type == AnswerTypeEnum.multiple_select:
                if not isinstance(answer_val, list): raise ValueError("Answer for multiple select must be a list.")
                if q_options:
                    for item in answer_val:
                        if not (isinstance(item, str) and item in q_options): raise ValueError(f"Invalid option '{item}'.")
            elif q_type == AnswerTypeEnum.input:
                if not isinstance(answer_val, str): raise ValueError("Answer for input must be a string.")
            elif q_type == AnswerTypeEnum.range:
                if not isinstance(answer_val, (int, float)): raise ValueError("Answer for range must be a number.")
                if q_options: 
                    min_val, max_val = q_options.get("min"), q_options.get("max")
                    if min_val is not None and answer_val < min_val: raise ValueError(f"Value {answer_val} is below minimum {min_val}.")
                    if max_val is not None and answer_val > max_val: raise ValueError(f"Value {answer_val} is above maximum {max_val}.")
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid answer for Q '{question_from_db['title']}': {ve}")
        
        answer_db_data = ans_payload.model_dump()
        answer_db_data.update({
            "survey_attempt_id": attempt_obj_id, "student_id": current_user.id,
            "answered_at": datetime.now(UTC), "score_achieved": None 
        })
        
        await answer_collection.replace_one(
            {"survey_attempt_id": attempt_obj_id, "qca_id": ans_payload.qca_id},
            answer_db_data, upsert=True
        )
        stored_answer_dict = await answer_collection.find_one({"survey_attempt_id": attempt_obj_id, "qca_id": ans_payload.qca_id})
        if stored_answer_dict:
            prepared_ans_dict = _prepare_student_answer_dict_for_out(stored_answer_dict.copy())
            processed_answers_out.append(StudentAnswerOut.model_validate(prepared_ans_dict))
    return processed_answers_out


@SurveyAttemptRouter.post("/{attempt_id}/submit", response_model=SurveyAttemptResultOut)
async def submit_survey_attempt(
    attempt_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(attempt_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attempt ID format.")

    attempt_collection = get_survey_attempt_collection()
    answer_collection = get_student_answer_collection()
    survey_collection = get_survey_collection()
    qca_collection = get_qca_collection()
    question_collection = get_question_collection()

    attempt_obj_id = PyObjectId(attempt_id)
    attempt_dict = await attempt_collection.find_one({"_id": attempt_obj_id, "student_id": current_user.id}) 

    if not attempt_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey attempt not found or not yours.")
    if attempt_dict["is_submitted"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey has already been submitted.")

    survey_dict_from_db = await survey_collection.find_one({"_id": attempt_dict["survey_id"]})
    if not survey_dict_from_db: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated survey not found.")    
    survey_obj = SurveyInDB.model_validate(survey_dict_from_db) 
    
    survey_courses_ids_pyobj = survey_obj.course_ids 

    student_answers_for_scoring_cursor = answer_collection.find({"survey_attempt_id": attempt_obj_id})
    answers_list_dicts_with_scores = [] 
    
    calculated_course_scores: Dict[str, float] = {str(cid): 0.0 for cid in survey_courses_ids_pyobj}

    async for student_answer_dict in student_answers_for_scoring_cursor:
        qca = await qca_collection.find_one({"_id": student_answer_dict["qca_id"]})
        if not qca: continue 
        question_dict_from_db = await question_collection.find_one({"_id": qca["question_id"]})
        if not question_dict_from_db: continue 

        answer_score = await calculate_score_for_answer(question_dict_from_db, student_answer_dict["answer_value"])
        
        await answer_collection.update_one(
            {"_id": student_answer_dict["_id"]},
            {"$set": {"score_achieved": answer_score}}
        )
        student_answer_dict["score_achieved"] = answer_score 
        answers_list_dicts_with_scores.append(student_answer_dict)
        
        course_id_for_qca_str = str(qca["course_id"])
        
        # MODIFIED: Apply AnswerAssociationTypeEnum logic
        answer_score_contribution = answer_score
        if qca.get("answer_association_type") == AnswerAssociationTypeEnum.negative.value:
            answer_score_contribution *= -1
            
        if course_id_for_qca_str in calculated_course_scores:
            calculated_course_scores[course_id_for_qca_str] += answer_score_contribution
        else: 
            print(f"Warning: QCA {qca['_id']} course {course_id_for_qca_str} not in survey's courses. Score not added to totals.")
    
    attempt_dict["course_scores"] = calculated_course_scores 

    # MODIFIED: Call updated feedback and outcome generation function
    final_course_fb, detailed_fb, overall_survey_fb, course_outcomes = await generate_all_feedback_and_outcomes_for_attempt(
        attempt_dict, survey_obj, answers_list_dicts_with_scores,
        qca_collection, question_collection
    )

    update_data_for_attempt = {
        "is_submitted": True, "submitted_at": datetime.now(UTC),
        "course_scores": calculated_course_scores,
        "course_feedback": final_course_fb,
        "detailed_feedback": detailed_fb,
        "overall_survey_feedback": overall_survey_fb,
        "course_outcome_categorization": course_outcomes # MODIFIED: Store outcomes
    }
    await attempt_collection.update_one({"_id": attempt_obj_id}, {"$set": update_data_for_attempt})

    updated_attempt_dict_from_db = await attempt_collection.find_one({"_id": attempt_obj_id})
    if not updated_attempt_dict_from_db: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve attempt after submission.")

    prepared_attempt_dict = _prepare_survey_attempt_dict_for_out(updated_attempt_dict_from_db.copy())
    result_out = SurveyAttemptResultOut.model_validate(prepared_attempt_dict)
    
    prepared_answers_list = []
    for ans_dict in answers_list_dicts_with_scores: 
        prepared_answers_list.append(
            StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(ans_dict.copy()))
        )
    result_out.answers = prepared_answers_list
    return result_out


@SurveyAttemptRouter.get("/{attempt_id}/results", response_model=SurveyAttemptResultOut)
async def get_survey_attempt_results(
    attempt_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(attempt_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attempt ID format.")
    
    attempt_collection = get_survey_attempt_collection()
    answer_collection = get_student_answer_collection()
    survey_collection = get_survey_collection() 

    attempt_dict = await attempt_collection.find_one({"_id": PyObjectId(attempt_id)})
    if not attempt_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey attempt not found.")

    is_owner = attempt_dict["student_id"] == current_user.id
    is_teacher_authorized = False
    if current_user.role == RoleEnum.teacher:
        survey_for_attempt = await survey_collection.find_one({"_id": attempt_dict["survey_id"]})
        if survey_for_attempt and survey_for_attempt["created_by"] == current_user.id:
            is_teacher_authorized = True

    if not (is_owner or is_teacher_authorized):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these results.")
    
    if not attempt_dict["is_submitted"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey results are not yet available (not submitted).")

    answers_list_dicts = await answer_collection.find({"survey_attempt_id": PyObjectId(attempt_id)}).to_list(length=None)
    
    prepared_attempt_dict = _prepare_survey_attempt_dict_for_out(attempt_dict.copy())
    result_out = SurveyAttemptResultOut.model_validate(prepared_attempt_dict)
    
    prepared_answers_list = []
    for ans_dict in answers_list_dicts:
        prepared_answers_list.append(
            StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(ans_dict.copy()))
        )
    result_out.answers = prepared_answers_list
    return result_out


@SurveyAttemptRouter.get("/my", response_model=List[SurveyAttemptOut])
async def list_my_survey_attempts(
    current_user: UserInDB = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 20,
    include_answers: bool = Query(False, description="Set to true to include answers for each attempt")
):
    attempt_collection = get_survey_attempt_collection()
    answer_collection = get_student_answer_collection()

    attempts_cursor = attempt_collection.find({"student_id": current_user.id}).skip(skip).limit(limit).sort("started_at", -1)
    attempts_list_dicts = await attempts_cursor.to_list(length=limit)
    
    results_out = []
    for attempt_dict_from_db in attempts_list_dicts:
        prepared_attempt_dict = _prepare_survey_attempt_dict_for_out(attempt_dict_from_db.copy())
        attempt_out = SurveyAttemptOut.model_validate(prepared_attempt_dict)
        
        if include_answers and attempt_out.is_submitted: 
            answers_dicts = await answer_collection.find({"survey_attempt_id": PyObjectId(attempt_out.id)}).to_list(length=None)
            prepared_answers_list = []
            for ans_dict in answers_dicts:
                prepared_answers_list.append(
                    StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(ans_dict.copy()))
                )
            attempt_out.answers = prepared_answers_list
        results_out.append(attempt_out)
    return results_out

@SurveyAttemptRouter.get("/by-survey/{survey_id}", response_model=List[SurveyAttemptOut])
async def list_attempts_for_survey(
    survey_id: str,
    current_user: UserInDB = Depends(require_teacher_role), 
    skip: int = 0,
    limit: int = 50,
    include_answers: bool = Query(False, description="Set to true to include answers for each attempt")
):
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid survey ID format.")
    
    survey_collection = get_survey_collection()
    attempt_collection = get_survey_attempt_collection()
    answer_collection = get_student_answer_collection()

    survey_obj_id = PyObjectId(survey_id)
    survey = await survey_collection.find_one({"_id": survey_obj_id})
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found.")
    
    if survey["created_by"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view attempts for this survey.")

    attempts_cursor = attempt_collection.find(
        {"survey_id": survey_obj_id, "is_submitted": True} 
    ).skip(skip).limit(limit).sort("submitted_at", -1)
    
    attempts_list_dicts = await attempts_cursor.to_list(length=limit)
    
    results_out = []
    for attempt_dict_from_db in attempts_list_dicts:
        prepared_attempt_dict = _prepare_survey_attempt_dict_for_out(attempt_dict_from_db.copy())
        attempt_out = SurveyAttemptOut.model_validate(prepared_attempt_dict)
        
        if include_answers: 
            answers_dicts = await answer_collection.find({"survey_attempt_id": PyObjectId(attempt_out.id)}).to_list(length=None)
            prepared_answers_list = []
            for ans_dict in answers_dicts:
                prepared_answers_list.append(
                    StudentAnswerOut.model_validate(_prepare_student_answer_dict_for_out(ans_dict.copy()))
                )
            attempt_out.answers = prepared_answers_list
        results_out.append(attempt_out)
    return results_out