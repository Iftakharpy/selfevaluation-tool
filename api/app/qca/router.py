# FilePath: api/app/qca/router.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId

from app.core.db import get_qca_collection, get_question_collection, get_course_collection
from app.users.auth import require_teacher_role
from app.users.data_types import UserInDB, PyObjectId as UserPyObjectId # Alias to avoid conflict if needed
from .data_types import QcaCreate, QcaUpdate, QcaOut, QcaInDB
# Assuming PyObjectId from app.users.data_types is the one used everywhere
from app.users.data_types import PyObjectId

QcaRouter = APIRouter()

@QcaRouter.post("/", response_model=QcaOut, status_code=status.HTTP_201_CREATED)
async def create_qca(
    qca_in: QcaCreate,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    qca_collection = get_qca_collection()
    question_collection = get_question_collection()
    course_collection = get_course_collection()

    # Validate existence of question_id and course_id
    question = await question_collection.find_one({"_id": qca_in.question_id})
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question with ID {qca_in.question_id} not found.")
    course = await course_collection.find_one({"_id": qca_in.course_id})
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with ID {qca_in.course_id} not found.")

    # Check if this specific association already exists
    existing_qca = await qca_collection.find_one({
        "question_id": qca_in.question_id,
        "course_id": qca_in.course_id
    })
    if existing_qca:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This question is already associated with this course.")

    qca_db_obj = QcaInDB(**qca_in.model_dump())
    result = await qca_collection.insert_one(qca_db_obj.model_dump(by_alias=True))
    
    created_qca_dict = await qca_collection.find_one({"_id": result.inserted_id})
    if not created_qca_dict:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create QCA.")
    
    if "_id" in created_qca_dict:
        created_qca_dict["id"] = str(created_qca_dict.pop("_id"))
        
    return QcaOut.model_validate(created_qca_dict)

@QcaRouter.get("/", response_model=List[QcaOut])
async def list_qcas(
    question_id: Optional[str] = Query(None, description="Filter by Question ID"),
    course_id: Optional[str] = Query(None, description="Filter by Course ID"),
    skip: int = 0,
    limit: int = 100,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    qca_collection = get_qca_collection()
    query_filter = {}
    if question_id:
        if not ObjectId.is_valid(question_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question_id format.")
        query_filter["question_id"] = PyObjectId(question_id)
    if course_id:
        if not ObjectId.is_valid(course_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course_id format.")
        query_filter["course_id"] = PyObjectId(course_id)

    qcas_cursor = qca_collection.find(query_filter).skip(skip).limit(limit)
    qcas_list_from_db = await qcas_cursor.to_list(length=limit)
    
    processed_qcas = []
    for qca_dict in qcas_list_from_db:
        if "_id" in qca_dict:
            qca_dict["id"] = str(qca_dict.pop("_id"))
        processed_qcas.append(QcaOut.model_validate(qca_dict))
    return processed_qcas

@QcaRouter.get("/{qca_id}", response_model=QcaOut)
async def get_qca(
    qca_id: str,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(qca_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QCA ID format.")
    
    qca_collection = get_qca_collection()
    qca_dict = await qca_collection.find_one({"_id": PyObjectId(qca_id)})
    if not qca_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QCA not found.")

    if "_id" in qca_dict:
        qca_dict["id"] = str(qca_dict.pop("_id"))
    return QcaOut.model_validate(qca_dict)

@QcaRouter.put("/{qca_id}", response_model=QcaOut)
async def update_qca(
    qca_id: str,
    qca_update: QcaUpdate,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(qca_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QCA ID format.")

    qca_collection = get_qca_collection()
    update_data = qca_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    existing_qca = await qca_collection.find_one({"_id": PyObjectId(qca_id)})
    if not existing_qca:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QCA not found to update.")

    updated_result = await qca_collection.update_one(
        {"_id": PyObjectId(qca_id)},
        {"$set": update_data}
    )
    
    final_qca_dict = await qca_collection.find_one({"_id": PyObjectId(qca_id)})
    if not final_qca_dict: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve QCA after update.")
    
    if "_id" in final_qca_dict:
        final_qca_dict["id"] = str(final_qca_dict.pop("_id"))
    return QcaOut.model_validate(final_qca_dict)

@QcaRouter.delete("/{qca_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qca(
    qca_id: str,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    if not ObjectId.is_valid(qca_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QCA ID format.")
    # TODO: Consider if deleting a QCA has implications for ongoing surveys or results.
    qca_collection = get_qca_collection()
    delete_result = await qca_collection.delete_one({"_id": PyObjectId(qca_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QCA not found.")
    return None