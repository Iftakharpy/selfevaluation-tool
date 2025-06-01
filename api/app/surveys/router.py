# FilePath: C:\Users\iftak\Desktop\jamk\2025 Spring\narsus-self-evaluation-tool\api\app\surveys\router.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, UTC

from app.core.db import (
    get_survey_collection, 
    get_course_collection, 
    get_qca_collection, 
    get_question_collection,
    get_survey_attempt_collection, 
    get_student_answer_collection 
)
from app.users.auth import require_teacher_role, get_current_active_user
from app.users.data_types import UserInDB, PyObjectId, RoleEnum
from .data_types import (
    SurveyCreate, SurveyUpdate, SurveyOut, SurveyInDB, SurveyQuestionDetail, ScoreFeedbackItem
)
from app.questions.data_types import AnswerTypeEnum 

SurveyRouter = APIRouter()

async def _get_survey_question_details(survey: SurveyInDB) -> List[SurveyQuestionDetail]:
    """Helper to fetch and format question details for a survey."""
    qca_collection = get_qca_collection()
    question_collection = get_question_collection()
    
    survey_questions_details: List[SurveyQuestionDetail] = []
    processed_question_ids = set() 

    if not survey.course_ids:
        return []

    qcas_cursor = qca_collection.find({"course_id": {"$in": survey.course_ids}})
    async for qca in qcas_cursor:
        question_id = qca["question_id"]
        # The set processed_question_ids ensures each question appears once, even if linked via multiple QCAs
        # to different courses within the same survey OR multiple times to the same course (though latter is less likely).
        # Current logic: if a question is tied to CourseA and CourseB (both in survey),
        # it will appear once, associated with the first QCA encountered.
        # If specific ordering or per-course context for *displaying* questions is needed, this might need adjustment.
        if question_id in processed_question_ids:
            continue 

        question = await question_collection.find_one({"_id": question_id})
        if question:
            sqd = SurveyQuestionDetail(
                qca_id=str(qca["_id"]),
                question_id=str(question["_id"]),
                course_id=str(qca["course_id"]), 
                title=question["title"],
                details=question.get("details"),
                answer_type=AnswerTypeEnum(question["answer_type"]),
                answer_options=question.get("answer_options")
            )
            survey_questions_details.append(sqd)
            processed_question_ids.add(question_id)
            
    # Current behavior: Questions are ordered by the database fetch order of QCAs.
    # For more robust or specific ordering (e.g., by course, then by question title, or manually defined),
    # additional logic would be needed here or by storing order information in the Survey/QCA.
    return survey_questions_details

def _prepare_survey_dict_for_out(survey_dict_from_db: dict) -> dict:
    """Converts MongoDB ObjectId fields to strings for SurveyOut model validation."""
    if "_id" in survey_dict_from_db:
        survey_dict_from_db["id"] = str(survey_dict_from_db.pop("_id"))
    if "created_by" in survey_dict_from_db and isinstance(survey_dict_from_db["created_by"], ObjectId):
        survey_dict_from_db["created_by"] = str(survey_dict_from_db["created_by"])
    if "course_ids" in survey_dict_from_db:
        survey_dict_from_db["course_ids"] = [str(cid) for cid in survey_dict_from_db["course_ids"]]
    
    # Ensure course_skill_total_score_thresholds keys (course_ids) are strings
    if "course_skill_total_score_thresholds" in survey_dict_from_db and survey_dict_from_db["course_skill_total_score_thresholds"]:
        new_thresholds = {}
        for k, v in survey_dict_from_db["course_skill_total_score_thresholds"].items():
            new_thresholds[str(k)] = v # Ensure key is string
        survey_dict_from_db["course_skill_total_score_thresholds"] = new_thresholds
    elif "course_skill_total_score_thresholds" not in survey_dict_from_db: # Ensure field exists for model validation
        survey_dict_from_db["course_skill_total_score_thresholds"] = {}


    return survey_dict_from_db

@SurveyRouter.post("/", response_model=SurveyOut, status_code=status.HTTP_201_CREATED)
async def create_survey(
    survey_in: SurveyCreate,
    current_user: UserInDB = Depends(require_teacher_role)
):
    survey_collection = get_survey_collection()
    course_collection = get_course_collection()

    if survey_in.course_ids:
        for course_id_obj in survey_in.course_ids:
            course = await course_collection.find_one({"_id": course_id_obj})
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Course with ID '{str(course_id_obj)}' not found."
                )
    
    # Validate course_skill_total_score_thresholds if provided
    if survey_in.course_skill_total_score_thresholds:
        for course_id_str, _ in survey_in.course_skill_total_score_thresholds.items():
            if not ObjectId.is_valid(course_id_str) or not any(PyObjectId(course_id_str) == cid for cid in survey_in.course_ids):
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid or non-survey course ID '{course_id_str}' in course_skill_total_score_thresholds."
                )

    survey_db_data = survey_in.model_dump()
    survey_db_data["created_by"] = current_user.id 
    
    # Convert string keys in course_skill_total_score_thresholds to PyObjectId for DB storage if needed
    # However, Pydantic model with Dict[str, ...] expects string keys.
    # If storing with ObjectId keys in DB, conversion needed here. Sticking to str keys for simplicity.
    
    survey_db_obj = SurveyInDB(**survey_db_data) 
    
    result = await survey_collection.insert_one(survey_db_obj.model_dump(by_alias=True))
    created_survey_dict_from_db = await survey_collection.find_one({"_id": result.inserted_id})
    
    if not created_survey_dict_from_db:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create survey.")
    
    prepared_dict = _prepare_survey_dict_for_out(created_survey_dict_from_db.copy()) 
    return SurveyOut.model_validate(prepared_dict)


@SurveyRouter.get("/", response_model=List[SurveyOut])
async def list_surveys(
    current_user: UserInDB = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    published_only: Optional[bool] = None
):
    survey_collection = get_survey_collection()
    query = {}

    if current_user.role == RoleEnum.student:
        query["is_published"] = True
    elif published_only is not None: # Teacher can filter
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

    survey_obj_for_logic = SurveyInDB.model_validate(survey_dict_from_db) 

    if current_user.role == RoleEnum.student and not survey_obj_for_logic.is_published:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Survey not published or access denied.")

    prepared_dict = _prepare_survey_dict_for_out(survey_dict_from_db.copy())
    survey_out_obj = SurveyOut.model_validate(prepared_dict) 

    if include_questions:
        survey_out_obj.questions = await _get_survey_question_details(survey_obj_for_logic) 
        
    return survey_out_obj


@SurveyRouter.put("/{survey_id}", response_model=SurveyOut)
async def update_survey(
    survey_id: str,
    survey_update: SurveyUpdate,
    current_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid survey ID format.")

    survey_collection = get_survey_collection()
    existing_survey_dict = await survey_collection.find_one({"_id": PyObjectId(survey_id)})
    if not existing_survey_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found.")
    
    if existing_survey_dict["created_by"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this survey.")

    update_data = survey_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    update_data["updated_at"] = datetime.now(UTC)

    # Validate course_ids if they are being updated
    if "course_ids" in update_data and update_data["course_ids"] is not None:
        course_collection = get_course_collection()
        for c_id_obj in update_data["course_ids"]: # These are PyObjectId from SurveyUpdate
            if not await course_collection.find_one({"_id": c_id_obj}):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with ID '{str(c_id_obj)}' not found in update.")

    # Validate course_skill_total_score_thresholds if provided in update
    if "course_skill_total_score_thresholds" in update_data and update_data["course_skill_total_score_thresholds"] is not None:
        # Use the effective course_ids (either from update or existing) for validation
        effective_course_ids_pyobj = update_data.get("course_ids", [PyObjectId(cid_str) for cid_str in existing_survey_dict.get("course_ids", [])])
        
        for course_id_str, _ in update_data["course_skill_total_score_thresholds"].items():
            if not ObjectId.is_valid(course_id_str) or not any(PyObjectId(course_id_str) == cid for cid in effective_course_ids_pyobj):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid or non-survey course ID '{course_id_str}' in course_skill_total_score_thresholds during update."
                )
        # Pydantic model expects Dict[str, List[ScoreFeedbackItem]], so keys are already strings.
        # If database stores ObjectId keys, conversion would be needed for $set. Sticking to string keys.

    await survey_collection.update_one({"_id": PyObjectId(survey_id)}, {"$set": update_data})
    updated_survey_dict_from_db = await survey_collection.find_one({"_id": PyObjectId(survey_id)})
    if not updated_survey_dict_from_db:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve survey after update.")
    
    prepared_dict = _prepare_survey_dict_for_out(updated_survey_dict_from_db.copy())
    return SurveyOut.model_validate(prepared_dict)

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
    
    # Check if survey has any submitted attempts. If so, prevent deletion.
    # A softer approach might be to "archive" the survey instead.
    attempt_collection = get_survey_attempt_collection()
    submitted_attempt = await attempt_collection.find_one({"survey_id": survey_obj_id, "is_submitted": True})
    if submitted_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete survey with submitted attempts. Consider archiving."
        )

    delete_result = await survey_collection.delete_one({"_id": survey_obj_id})
    if delete_result.deleted_count == 0:
        # This case should be caught by the find_one above, but as a safeguard.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found or already deleted.")
    
    # Cascade delete associated survey attempts (unsubmitted) and their answers
    student_answer_collection = get_student_answer_collection()
    
    attempts_to_delete_cursor = attempt_collection.find({"survey_id": survey_obj_id}) # Will only be unsubmitted ones
    async for attempt in attempts_to_delete_cursor:
        await student_answer_collection.delete_many({"survey_attempt_id": attempt["_id"]})
    await attempt_collection.delete_many({"survey_id": survey_obj_id})
    
    return None
    