# FilePath: api/app/questions/router.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from bson import ObjectId

from app.core.db import get_course_collection # Re-using for now, should be get_question_collection
# We need to add get_question_collection to core/db.py
from app.users.auth import require_teacher_role
from app.users.data_types import UserInDB
from .data_types import QuestionCreate, QuestionUpdate, QuestionOut, QuestionInDB, PyObjectId

QuestionRouter = APIRouter()

# Placeholder for get_question_collection - MUST BE ADDED TO core/db.py
def get_question_collection():
    # This is a temporary placeholder. Replace with actual implementation in core/db.py
    from app.core.db import MONGO_DB
    if MONGO_DB.db is None:
        raise Exception("Database not initialized.")
    return MONGO_DB.db["questions"]

@QuestionRouter.post("/", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_in: QuestionCreate,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    question_collection = get_question_collection()
    
    # Optional: Check for duplicate question titles or other unique constraints if needed
    # existing_question = await question_collection.find_one({"title": question_in.title})
    # if existing_question:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question with this title already exists.")

    question_db_obj = QuestionInDB(**question_in.model_dump())
    result = await question_collection.insert_one(question_db_obj.model_dump(by_alias=True))
    
    created_question_dict = await question_collection.find_one({"_id": result.inserted_id})
    if not created_question_dict:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create question.")
    
    # Prepare for QuestionOut
    if "_id" in created_question_dict:
        created_question_dict["id"] = str(created_question_dict.pop("_id"))
        
    return QuestionOut.model_validate(created_question_dict)

@QuestionRouter.get("/", response_model=List[QuestionOut])
async def list_questions(
    skip: int = 0,
    limit: int = 100,
    teacher_user: UserInDB = Depends(require_teacher_role) # Only teachers can list all questions for now
):
    question_collection = get_question_collection()
    questions_cursor = question_collection.find().skip(skip).limit(limit)
    questions_list_from_db = await questions_cursor.to_list(length=limit)
    
    processed_questions = []
    for q_dict in questions_list_from_db:
        if "_id" in q_dict:
            q_dict["id"] = str(q_dict.pop("_id"))
        processed_questions.append(QuestionOut.model_validate(q_dict))
    return processed_questions

@QuestionRouter.get("/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: str,
    teacher_user: UserInDB = Depends(require_teacher_role) # Or current_active_user if students can see them directly
):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question ID format.")
    
    question_collection = get_question_collection()
    question_dict = await question_collection.find_one({"_id": PyObjectId(question_id)})
    if not question_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    if "_id" in question_dict:
        question_dict["id"] = str(question_dict.pop("_id"))
    return QuestionOut.model_validate(question_dict)

@QuestionRouter.put("/{question_id}", response_model=QuestionOut)
async def update_question(
    question_id: str,
    question_update: QuestionUpdate,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question ID format.")

    question_collection = get_question_collection()
    
    update_data = question_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    # First, check if the question exists before attempting an update
    # This also helps in the case where modified_count is 0 because the document wasn't found
    # for the update operation itself.
    to_update_doc = await question_collection.find_one({"_id": PyObjectId(question_id)})
    if not to_update_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found to update.")

    updated_result = await question_collection.update_one(
        {"_id": PyObjectId(question_id)}, # Filter to find the document
        {"$set": update_data}             # The update to apply
    )

    # updated_result.matched_count should be 1 if the above find_one succeeded.
    # If matched_count is 0 here, it means something went wrong between find_one and update_one,
    # or the document was deleted in between (unlikely in typical scenarios).
    if updated_result.matched_count == 0:
        # This case should ideally be caught by the initial find_one check.
        # If we reach here, it's an unexpected state.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found during update operation (unexpected).")
    
    # If modified_count is 0 but matched_count is 1, it means the document was found
    # but the update data resulted in no actual change to the document.
    # In this case, we fetch and return the (unchanged) document.
    
    # Fetch the potentially updated document to return
    # This is always a good idea to return the actual state from the DB.
    final_question_dict = await question_collection.find_one({"_id": PyObjectId(question_id)})
    
    # This check should ideally not be strictly necessary if the update was successful
    # and the document was matched. But for safety:
    if not final_question_dict: 
        # This would be a very strange state, indicating the document disappeared after update.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve question after update.")
    
    # Prepare for QuestionOut model validation
    if "_id" in final_question_dict: # Check if "_id" is in the dict before accessing
        final_question_dict["id"] = str(final_question_dict.pop("_id"))
        
    return QuestionOut.model_validate(final_question_dict)

@QuestionRouter.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: str,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question ID format.")

    question_collection = get_question_collection()
    # TODO: Check if this question is part of any QuestionCourseAssociation or Survey before deleting,
    # or handle cascading deletes/archiving. For now, direct delete.
    delete_result = await question_collection.delete_one({"_id": PyObjectId(question_id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    return None
