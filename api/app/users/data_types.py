from __future__ import annotations
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    ValidationInfo, # Needed for PyObjectId.validate
    ConfigDict,
    # GetCoreSchemaHandler # Not used if not defining __get_pydantic_core_schema__
)
from pydantic.functional_validators import BeforeValidator # Needed for Annotated
# from pydantic_core import core_schema, PydanticCustomError # Not used if not defining __get_pydantic_core_schema__
from typing import Optional, Annotated, Any # Annotated is used
from enum import Enum
from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, PydanticCustomError, core_schema


class PyObjectId(ObjectId):
    """
    Custom type for PyMongo's ObjectId to be used with Pydantic.
    """

    @classmethod
    def __get_validators__(cls):
        # This part is for Pydantic V1 compatibility,
        # but for V2, __get_pydantic_core_schema__ is preferred.
        # Keeping it for backward compatibility or if there are other uses.
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        # This validator is used by __get_validators__ for V1.
        # For V2, the core_schema validation functions handle this.
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
            raise ValueError("Invalid ObjectId string")
        raise ValueError("ObjectId must be an ObjectId instance or a valid string representation")


    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """
        Returns a Pydantic CoreSchema for PyObjectId.
        This defines how Pydantic should serialize and deserialize the type.
        """
        def validate_from_str(value: str) -> ObjectId:
            # This function is used by the core_schema to validate string inputs
            if not ObjectId.is_valid(value):
                raise PydanticCustomError('object_id', 'Invalid ObjectId string')
            return ObjectId(value)

        # Defines how to serialize PyObjectId to a string for JSON output
        # and how to validate from different input types.
        schema = core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(), # Corrected: use str_schema()
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]),
            serialization=core_schema.to_string_ser_schema(), # Corrected: use to_string_ser_schema()
        )
        # Apply the final validation to ensure the result is an instance of PyObjectId
        # or handle any other specific post-validation logic.
        # For a simple ObjectId wrapper, the above schema might be sufficient
        # if the input directly becomes an ObjectId. If PyObjectId itself is
        # meant to be the final output type, an after_validator is good.
        return core_schema.no_info_after_validator_function(cls, schema)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ObjectId):
            return super().__eq__(other)
        return NotImplemented

    def __hash__(self) -> int:
        return super().__hash__()


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
        arbitrary_types_allowed=True # IMPORTANT: Allows PyObjectId as a field type
    )

class UserCreate(UserBase):
    password: str

class UserInDBBase(UserBase):
    id: Annotated[PyObjectId, BeforeValidator(PyObjectId.validate)] = Field(
        default_factory=PyObjectId, 
        alias="_id"
        # json_schema_extra={"example": "..."} # Can be added to PyObjectId.__get_pydantic_json_schema__
    )

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