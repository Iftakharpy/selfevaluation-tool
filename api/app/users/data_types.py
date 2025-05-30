# FilePath: api/app/users/data_types.py
from __future__ import annotations # Keep this for forward refs if needed
from pydantic import BaseModel, Field, EmailStr, ValidationInfo, ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing import Optional, Annotated, Any
from enum import Enum
from bson import ObjectId



class PyObjectId(ObjectId):
    @classmethod
    def validate(cls, v: Any, info: ValidationInfo) -> PyObjectId: # Ensure return type is PyObjectId
        if isinstance(v, PyObjectId): return v
        if isinstance(v, ObjectId): return cls(v)
        if isinstance(v, str) and ObjectId.is_valid(v): return cls(v)
        field_name = "unknown_field"
        if info and hasattr(info, 'field_name') and info.field_name:
            field_name = info.field_name
        raise ValueError(f"Invalid ObjectId for field '{field_name}': '{v}' is not a valid ObjectId or string representation.")

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        # This helps represent it as a string in OpenAPI
        json_schema = handler(core_schema)
        json_schema.update(type="string", example="60b8d295f1d2b3c4d5e6f7a8")
        return json_schema

    # OPTION 2 would be to add __get_pydantic_core_schema__ here.
    # For now, we rely on arbitrary_types_allowed in models using PyObjectId.

class RoleEnum(str, Enum):
    student = "student"
    teacher = "teacher"

class UserBase(BaseModel):
    username: EmailStr
    display_name: str
    role: RoleEnum
    photo_url: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True # This SHOULD allow PyObjectId in subclasses
    )

class UserCreate(UserBase):
    password: str

class UserInDBBase(UserBase):
    id: Annotated[PyObjectId, BeforeValidator(PyObjectId.validate)] = Field(
        default_factory=PyObjectId, # Corrected from lambda: PyObjectId()
        alias="_id",
        json_schema_extra={"example": "60b8d295f1d2b3c4d5e6f7a8"}
    )
    # model_config with arbitrary_types_allowed is inherited from UserBase

class UserInDB(UserInDBBase):
    password_hash: str

class UserOut(UserBase):
    id: str
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "60b8d295f1d2b3c4d5e6f7a8",
                "display_name": "John Doe",
                "username": "john.doe@jamk.fi",
                "role": "student",
                "photo_url": "http://example.com/photo.jpg",
            }
        }
    )

class UserLogin(BaseModel):
    username: EmailStr
    password: str

class TokenData(BaseModel):
    username: Optional[str] = None