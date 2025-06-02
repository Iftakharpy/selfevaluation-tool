from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from bson import ObjectId

from app.core.db import get_question_collection, get_qca_collection # MODIFIED: Added get_qca_collection
from app.users.auth import require_teacher_role
from app.users.data_types import UserInDB
from .data_types import QuestionCreate, QuestionUpdate, QuestionOut, QuestionInDB, PyObjectId

QuestionRouter = APIRouter()

# get_question_collection is already in core/db.py, no need for placeholder

@QuestionRouter.post("/", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_in: QuestionCreate,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    question_collection = get_question_collection()
    
    question_db_obj = QuestionInDB(**question_in.model_dump())
    result = await question_collection.insert_one(question_db_obj.model_dump(by_alias=True))
    
    created_question_dict = await question_collection.find_one({"_id": result.inserted_id})
    if not created_question_dict:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create question.")
    
    if "_id" in created_question_dict:
        created_question_dict["id"] = str(created_question_dict.pop("_id"))
        
    return QuestionOut.model_validate(created_question_dict)

# @QuestionRouter.get("/", response_model=List[QuestionOut])
# async def list_questions(
#     skip: int = 0,
#     limit: int = 100,
#     teacher_user: UserInDB = Depends(require_teacher_role) 
# ):
#     question_collection = get_question_collection()
#     questions_cursor = question_collection.find().skip(skip).limit(limit)
#     questions_list_from_db = await questions_cursor.to_list(length=limit)
    
#     processed_questions = []
#     for q_dict in questions_list_from_db:
#         if "_id" in q_dict:
#             q_dict["id"] = str(q_dict.pop("_id"))
#         processed_questions.append(QuestionOut.model_validate(q_dict))
#     return processed_questions

@QuestionRouter.get("/", response_model=List[QuestionOut])
async def list_questions(
    skip: int = 0,
    limit: int = 10, # Reduce limit for easier debugging
    teacher_user: UserInDB = Depends(require_teacher_role) 
):
    question_collection = get_question_collection()
    questions_cursor = question_collection.find().skip(skip).limit(limit)
    questions_list_from_db = await questions_cursor.to_list(length=limit)
    
    print(f"DEBUG: Fetched {len(questions_list_from_db)} raw documents from DB.")
    
    processed_questions = []
    for i, q_dict_raw in enumerate(questions_list_from_db):
        print(f"\nDEBUG: Processing document {i}: {q_dict_raw}")
        q_dict_for_validation = q_dict_raw.copy() # Work on a copy
        if "_id" in q_dict_for_validation:
            q_dict_for_validation["id"] = str(q_dict_for_validation.pop("_id"))
        
        try:
            # This is where Pydantic validation happens for each item
            validated_question = QuestionOut.model_validate(q_dict_for_validation)
            processed_questions.append(validated_question)
            print(f"DEBUG: Document {i} validated successfully.")
        except Exception as e: # Catch Pydantic's ValidationError or others
            print(f"!!!!!!!! ERROR VALIDATING DOCUMENT {i} !!!!!!!!")
            print(f"Document data: {q_dict_for_validation}")
            print(f"Validation Error: {e}")
            # Optionally, re-raise to see the full FastAPI error page for this specific doc
            # raise HTTPException(status_code=500, detail=f"Validation error in doc {i}: {e}") 
            # Or just skip it for now to see if others pass
            continue # Skip this problematic document
    
    print(f"DEBUG: Successfully processed {len(processed_questions)} documents.")
    return processed_questions


@QuestionRouter.get("/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: str,
    teacher_user: UserInDB = Depends(require_teacher_role) 
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

    to_update_doc = await question_collection.find_one({"_id": PyObjectId(question_id)})
    if not to_update_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found to update.")

    updated_result = await question_collection.update_one(
        {"_id": PyObjectId(question_id)}, 
        {"$set": update_data}             
    )

    if updated_result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found during update operation (unexpected).")
    
    final_question_dict = await question_collection.find_one({"_id": PyObjectId(question_id)})
    
    if not final_question_dict: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve question after update.")
    
    if "_id" in final_question_dict: 
        final_question_dict["id"] = str(final_question_dict.pop("_id"))
        
    return QuestionOut.model_validate(final_question_dict)

@QuestionRouter.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: str,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question ID format.")

    question_obj_id = PyObjectId(question_id)
    question_collection = get_question_collection()
    qca_collection = get_qca_collection()

    # Check if question is part of any QCA. If so, prevent deletion or delete QCAs.
    # For now, we'll delete associated QCAs.
    # A stricter approach might be to prevent deletion if it's in a QCA used by submitted surveys.
    associated_qcas = await qca_collection.find({"question_id": question_obj_id}).to_list(length=None)
    if associated_qcas:
        # Potentially add more complex checks here if needed, e.g., if any of these QCAs are in submitted survey attempts.
        # For now, simple cascade to QCAs.
        await qca_collection.delete_many({"question_id": question_obj_id})
        # print(f"Deleted QCAs associated with question {question_id}")

    delete_result = await question_collection.delete_one({"_id": question_obj_id})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    return None
    