# FilePath: api/app/courses/router.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from bson import ObjectId # For validating ObjectId strings from path

from app.core.db import get_course_collection
from app.users.auth import get_current_active_user, require_teacher_role 
from app.users.data_types import UserInDB # For type hinting current_user
from .data_types import CourseCreate, CourseOut, CourseUpdate, CourseInDB, PyObjectId

CourseRouter = APIRouter()

@CourseRouter.post("/", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_in: CourseCreate,
    teacher_user: UserInDB = Depends(require_teacher_role)
):
    course_collection = get_course_collection()
    existing_course = await course_collection.find_one({"code": course_in.code})
    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with code '{course_in.code}' already exists."
        )

    course_db_obj = CourseInDB(**course_in.model_dump())
    result = await course_collection.insert_one(course_db_obj.model_dump(by_alias=True))

    created_course_dict = await course_collection.find_one({"_id": result.inserted_id})
    if not created_course_dict:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create course.")

    # Prepare dict for CourseOut validation if populate_by_name isn't working
    # Ensure 'id' key exists and '_id' is removed or ignored if not needed by CourseOut
    if "_id" in created_course_dict:
        created_course_dict["id"] = str(created_course_dict.pop("_id")) # Convert ObjectId to str and rename key

    return CourseOut.model_validate(created_course_dict) # Now created_course_dict has 'id'

# Apply similar logic for get_course and update_course where CourseOut.model_validate is used
# on a dictionary fetched from the DB.

@CourseRouter.get("/{course_id}", response_model=CourseOut)
async def get_course(
    course_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID format.")
        
    course_collection = get_course_collection()
    # Assuming PyObjectId is correctly defined and used in CourseInDB
    course_dict_from_db = await course_collection.find_one({"_id": PyObjectId(course_id)}) 
    if not course_dict_from_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
    
    # Ensure 'id' is present for CourseOut validation
    if "_id" in course_dict_from_db:
         course_dict_from_db["id"] = str(course_dict_from_db.pop("_id"))

    return CourseOut.model_validate(course_dict_from_db)


@CourseRouter.get("/", response_model=List[CourseOut])
async def list_courses(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user)
):
    course_collection = get_course_collection()
    courses_cursor = course_collection.find().skip(skip).limit(limit)
    courses_list_from_db = await courses_cursor.to_list(length=limit) # Renamed for clarity
    
    # Prepare each dictionary for CourseOut validation
    processed_courses_out = []
    for course_dict_item in courses_list_from_db:
        if "_id" in course_dict_item:
            course_dict_item["id"] = str(course_dict_item.pop("_id"))
        processed_courses_out.append(CourseOut.model_validate(course_dict_item)) 
    
    return processed_courses_out

# @CourseRouter.get("/{course_id}", response_model=CourseOut)
# async def get_course(
#     course_id: str,
#     current_user: UserInDB = Depends(get_current_active_user) # All authenticated users can get by ID
# ):
#     if not ObjectId.is_valid(course_id):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID format.")
        
#     course_collection = get_course_collection()
#     course_dict = await course_collection.find_one({"_id": PyObjectId(course_id)}) # Use PyObjectId to ensure conversion
#     if not course_dict:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
    
#     return CourseOut.model_validate(course_dict)


@CourseRouter.put("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: str,
    course_update: CourseUpdate,
    teacher_user: UserInDB = Depends(require_teacher_role) # Only teachers can update
):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID format.")

    course_collection = get_course_collection()
    existing_course = await course_collection.find_one({"_id": PyObjectId(course_id)})
    if not existing_course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    update_data = course_update.model_dump(exclude_unset=True) # Only include fields that are set
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    # If code is being updated, check for uniqueness
    if "code" in update_data and update_data["code"] != existing_course.get("code"):
        colliding_course = await course_collection.find_one({"code": update_data["code"], "_id": {"$ne": PyObjectId(course_id)}})
        if colliding_course:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another course with code '{update_data['code']}' already exists."
            )

    updated_result = await course_collection.update_one(
        {"_id": PyObjectId(course_id)},
        {"$set": update_data}
    )

    if updated_result.modified_count == 0 and not updated_result.matched_count: # Check if it was found at all
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found or no changes made.")
    
    updated_course_dict_from_db = await course_collection.find_one({"_id": PyObjectId(course_id)})
    if not updated_course_dict_from_db:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve updated course.")
    
    if "_id" in updated_course_dict_from_db:
        updated_course_dict_from_db["id"] = str(updated_course_dict_from_db.pop("_id"))
        
    return CourseOut.model_validate(updated_course_dict_from_db)


@CourseRouter.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: str,
    teacher_user: UserInDB = Depends(require_teacher_role) # Only teachers can delete
):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID format.")

    course_collection = get_course_collection()
    delete_result = await course_collection.delete_one({"_id": PyObjectId(course_id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
    
    # No content to return for 204
    return None
