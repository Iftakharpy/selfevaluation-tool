# FilePath: api/app/courses/data_types.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.users.data_types import PyObjectId 

class CourseBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, examples=["Introduction to Python"])
    code: str = Field(..., min_length=2, max_length=20, examples=["PY101"])
    description: Optional[str] = Field(None, max_length=500, examples=["A beginner course on Python programming."])

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True # Good for any *other* custom types
    )

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    
    model_config = ConfigDict(
        populate_by_name=True
    )

class CourseInDBBase(CourseBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

class CourseInDB(CourseInDBBase):
    pass

class CourseOut(CourseBase):
    id: str
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "60c72b2f9b1e8b001c8e4d8a",
                "name": "Advanced Web Development",
                "code": "WEB303",
                "description": "Covers advanced topics in web development including APIs and frameworks."
            }
        }
    )