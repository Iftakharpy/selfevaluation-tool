# api/app/surveys/router.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, UTC
import random

from app.core.db import (
    get_survey_collection, 
    get_course_collection, 
    get_qca_collection, 
    get_question_collection,
    get_survey_attempt_collection, # ADDED IMPORT
    get_student_answer_collection  # ADDED IMPORT
)
from app.users.auth import require_teacher_role, get_current_active_user
from app.users.data_types import UserInDB, PyObjectId, RoleEnum
from .data_types import (
    SurveyCreate, SurveyUpdate, SurveyOut, SurveyInDB, SurveyQuestionDetail, 
    ScoreFeedbackItem, OutcomeThresholdItem
)
from app.questions.data_types import AnswerTypeEnum
from app.core.settings import STANDARD_QUESTION_MAX_SCORE # IMPORTED CONSTANT

SurveyRouter = APIRouter()

async def _get_survey_question_details(survey: SurveyInDB) -> List[SurveyQuestionDetail]:
    qca_collection = get_qca_collection()
    question_collection = get_question_collection()
    
    survey_questions_details: List[SurveyQuestionDetail] = []
    # processed_question_ids_in_survey = set() # Renamed for clarity

    if not survey.course_ids:
        return []

    qcas_for_survey_courses_cursor = qca_collection.find({"course_id": {"$in": survey.course_ids}})
    
    question_context_map: Dict[PyObjectId, Dict[str, Any]] = {}

    async for qca in qcas_for_survey_courses_cursor:
        question_id = qca["question_id"]
        if question_id not in question_context_map:
            question_context_map[question_id] = {
                "qca_id": str(qca["_id"]),
                "course_id": str(qca["course_id"]) 
            }

    for question_id, context_info in question_context_map.items():
        question = await question_collection.find_one({"_id": question_id})
        if question:
            sqd = SurveyQuestionDetail(
                qca_id=context_info["qca_id"],
                question_id=str(question["_id"]),
                course_id=context_info["course_id"], 
                title=question["title"],
                details=question.get("details"),
                answer_type=AnswerTypeEnum(question["answer_type"]),
                answer_options=question.get("answer_options")
            )
            survey_questions_details.append(sqd)
    
    random.shuffle(survey_questions_details)
    return survey_questions_details

def _prepare_survey_dict_for_out(survey_dict_from_db: dict) -> dict:
    if "_id" in survey_dict_from_db:
        survey_dict_from_db["id"] = str(survey_dict_from_db.pop("_id"))
    if "created_by" in survey_dict_from_db and isinstance(survey_dict_from_db["created_by"], ObjectId):
        survey_dict_from_db["created_by"] = str(survey_dict_from_db["created_by"])
    
    if "course_ids" in survey_dict_from_db and survey_dict_from_db["course_ids"]:
        survey_dict_from_db["course_ids"] = [str(cid) for cid in survey_dict_from_db["course_ids"]]
    
    for field_name in ["course_skill_total_score_thresholds", "course_outcome_thresholds", "max_scores_per_course"]:
        if field_name in survey_dict_from_db and survey_dict_from_db[field_name] is not None:
            new_dict = {}
            for k, v in survey_dict_from_db[field_name].items():
                new_dict[str(k)] = v 
            survey_dict_from_db[field_name] = new_dict
        elif survey_dict_from_db.get(field_name) is None: 
             survey_dict_from_db[field_name] = {}
    
    if survey_dict_from_db.get("max_overall_survey_score") is None:
        survey_dict_from_db["max_overall_survey_score"] = None


    return survey_dict_from_db

def _validate_threshold_keys(
    threshold_dict: Optional[Dict[str, List[Any]]], 
    survey_course_ids_pyobj: List[PyObjectId], 
    field_name: str
):
    if threshold_dict:
        for course_id_str_key in threshold_dict.keys():
            if not ObjectId.is_valid(course_id_str_key):
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid course ID format '{course_id_str_key}' as key in {field_name}."
                )
            if not any(PyObjectId(course_id_str_key) == survey_cid_obj for survey_cid_obj in survey_course_ids_pyobj):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Course ID key '{course_id_str_key}' in {field_name} is not associated with this survey."
                )

async def _calculate_and_set_max_scores(
    survey_data: dict, 
    qca_collection
):
    survey_course_ids_pyobj = survey_data.get("course_ids", []) 
    if not survey_course_ids_pyobj:
        survey_data["max_scores_per_course"] = {}
        survey_data["max_overall_survey_score"] = 0.0
        return

    temp_max_course_scores: Dict[PyObjectId, float] = {cid: 0.0 for cid in survey_course_ids_pyobj}
    unique_questions_in_survey_for_overall_score: set[PyObjectId] = set()
    
    processed_q_for_course_calc: set[tuple[PyObjectId, PyObjectId]] = set()

    if survey_course_ids_pyobj:
        qcas_cursor = qca_collection.find({"course_id": {"$in": survey_course_ids_pyobj}})
        async for qca in qcas_cursor:
            question_id: PyObjectId = qca["question_id"]
            course_id: PyObjectId = qca["course_id"]

            if course_id in temp_max_course_scores:
                if (question_id, course_id) not in processed_q_for_course_calc:
                    temp_max_course_scores[course_id] += STANDARD_QUESTION_MAX_SCORE
                    processed_q_for_course_calc.add((question_id, course_id))
            
            unique_questions_in_survey_for_overall_score.add(question_id)

    survey_data["max_scores_per_course"] = {str(cid): score for cid, score in temp_max_course_scores.items()}
    survey_data["max_overall_survey_score"] = float(len(unique_questions_in_survey_for_overall_score) * STANDARD_QUESTION_MAX_SCORE)


@SurveyRouter.post("/", response_model=SurveyOut, status_code=status.HTTP_201_CREATED)
async def create_survey(
    survey_in: SurveyCreate,
    current_user: UserInDB = Depends(require_teacher_role)
):
    survey_collection = get_survey_collection()
    course_collection = get_course_collection()
    qca_collection = get_qca_collection()
    
    valid_course_ids_pyobj: List[PyObjectId] = survey_in.course_ids # Already List[PyObjectId]
    if valid_course_ids_pyobj:
        for course_id_obj in valid_course_ids_pyobj:
            course = await course_collection.find_one({"_id": course_id_obj})
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Course with ID '{str(course_id_obj)}' not found."
                )
    
    _validate_threshold_keys(survey_in.course_skill_total_score_thresholds, valid_course_ids_pyobj, "course_skill_total_score_thresholds")
    _validate_threshold_keys(survey_in.course_outcome_thresholds, valid_course_ids_pyobj, "course_outcome_thresholds")
            
    survey_db_data = survey_in.model_dump(exclude={"max_scores_per_course", "max_overall_survey_score"}, exclude_none=True)
    survey_db_data["created_by"] = current_user.id
    # survey_db_data["course_ids"] already set as List[PyObjectId] from survey_in

    await _calculate_and_set_max_scores(survey_db_data, qca_collection)
            
    survey_db_obj = SurveyInDB(**survey_db_data) 
    result = await survey_collection.insert_one(survey_db_obj.model_dump(by_alias=True))
    created_survey_doc = await survey_collection.find_one({"_id": result.inserted_id})
    
    if not created_survey_doc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create survey.")
    
    prepared_dict = _prepare_survey_dict_for_out(created_survey_doc.copy()) 
    return SurveyOut.model_validate(prepared_dict)


@SurveyRouter.put("/{survey_id}", response_model=SurveyOut)
async def update_survey(
    survey_id: str,
    survey_update_payload: SurveyUpdate,
    current_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid survey ID format.")

    survey_collection = get_survey_collection()
    qca_collection = get_qca_collection()
    course_collection = get_course_collection()
    
    survey_obj_id = PyObjectId(survey_id)
    existing_survey_doc = await survey_collection.find_one({"_id": survey_obj_id})
    if not existing_survey_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found.")
    
    if existing_survey_doc["created_by"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this survey.")

    update_data = survey_update_payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    update_data["updated_at"] = datetime.now(UTC)

    effective_course_ids_pyobj: List[PyObjectId]
    if "course_ids" in update_data and update_data["course_ids"] is not None:
        validated_new_course_ids = []
        for c_id_obj in update_data["course_ids"]: 
            if not await course_collection.find_one({"_id": c_id_obj}):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with ID '{str(c_id_obj)}' not found in update.")
            validated_new_course_ids.append(c_id_obj)
        effective_course_ids_pyobj = validated_new_course_ids
    else:
        effective_course_ids_pyobj = existing_survey_doc.get("course_ids", [])

    if "course_skill_total_score_thresholds" in update_data:
         _validate_threshold_keys(update_data["course_skill_total_score_thresholds"], effective_course_ids_pyobj, "course_skill_total_score_thresholds")
    if "course_outcome_thresholds" in update_data:
         _validate_threshold_keys(update_data["course_outcome_thresholds"], effective_course_ids_pyobj, "course_outcome_thresholds")

    data_for_max_calc = existing_survey_doc.copy()
    for key, value in update_data.items():
        data_for_max_calc[key] = value
    data_for_max_calc["course_ids"] = effective_course_ids_pyobj 

    await _calculate_and_set_max_scores(data_for_max_calc, qca_collection)
    
    update_data["max_scores_per_course"] = data_for_max_calc["max_scores_per_course"]
    update_data["max_overall_survey_score"] = data_for_max_calc["max_overall_survey_score"]
    
    await survey_collection.update_one({"_id": survey_obj_id}, {"$set": update_data})
    updated_survey_doc = await survey_collection.find_one({"_id": survey_obj_id})
    if not updated_survey_doc:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve survey after update.")
    
    prepared_dict = _prepare_survey_dict_for_out(updated_survey_doc.copy())
    return SurveyOut.model_validate(prepared_dict)

@SurveyRouter.get("/", response_model=List[SurveyOut])
async def list_surveys(
    current_user: UserInDB = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    published_only: Optional[bool] = Query(None, description="Filter by published status. Student role always sees only published.")
):
    survey_collection = get_survey_collection()
    query: Dict[str, Any] = {}

    if current_user.role == RoleEnum.student:
        query["is_published"] = True
    elif published_only is not None: 
        query["is_published"] = published_only
        
    surveys_cursor = survey_collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    surveys_list_from_db = await surveys_cursor.to_list(length=limit)
    
    return [_prepare_survey_dict_for_out(s.copy()) for s in surveys_list_from_db] 


@SurveyRouter.get("/{survey_id}", response_model=SurveyOut)
async def get_survey(
    survey_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    include_questions: bool = Query(False, description="Set to true to include question details")
):
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid survey ID format.")
    
    survey_collection = get_survey_collection()
    survey_dict_from_db = await survey_collection.find_one({"_id": PyObjectId(survey_id)})
    if not survey_dict_from_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found.")

    try:
        survey_obj_for_logic = SurveyInDB.model_validate(survey_dict_from_db)
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Survey data integrity error: {e}")

    if current_user.role == RoleEnum.student and not survey_obj_for_logic.is_published:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Survey not published or access denied.")

    prepared_dict = _prepare_survey_dict_for_out(survey_dict_from_db.copy())
    survey_out_obj = SurveyOut.model_validate(prepared_dict) 

    if include_questions:
        survey_out_obj.questions = await _get_survey_question_details(survey_obj_for_logic) 
        
    return survey_out_obj

@SurveyRouter.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey(
    survey_id: str,
    current_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid survey ID format.")
    
    survey_obj_id = PyObjectId(survey_id)
    survey_collection = get_survey_collection()
    existing_survey = await survey_collection.find_one({"_id": survey_obj_id})
    if not existing_survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found.")

    if existing_survey["created_by"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this survey.")
    
    attempt_collection = get_survey_attempt_collection()
    submitted_attempt = await attempt_collection.find_one({"survey_id": survey_obj_id, "is_submitted": True})
    if submitted_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete survey with submitted attempts. Consider archiving."
        )

    delete_result = await survey_collection.delete_one({"_id": survey_obj_id})
    if delete_result.deleted_count == 0: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found or already deleted unexpectedly.")
    
    # Clean up associated attempts and their answers if the survey is deleted
    student_answer_collection = get_student_answer_collection()
    attempts_to_delete_cursor = attempt_collection.find({"survey_id": survey_obj_id}) 
    async for attempt in attempts_to_delete_cursor:
        await student_answer_collection.delete_many({"survey_attempt_id": attempt["_id"]})
    await attempt_collection.delete_many({"survey_id": survey_obj_id})
    
    return None