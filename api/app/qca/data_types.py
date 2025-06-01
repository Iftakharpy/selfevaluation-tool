from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated, List
from bson import ObjectId
from enum import Enum

from app.users.data_types import PyObjectId # For referencing User, Course, Question IDs
from app.questions.data_types import ScoreFeedbackItem # Re-use from questions
from pydantic.functional_validators import BeforeValidator

class AnswerAssociationTypeEnum(str, Enum):
    positive = "positive" # Correct answer contributes positively to course skill
    negative = "negative" # Correct answer might indicate skill is already present, thus negative towards needing the course

class QcaBase(BaseModel):
    question_id: PyObjectId = Field(..., description="Reference to the Question.")
    course_id: PyObjectId = Field(..., description="Reference to the Course.")
    answer_association_type: AnswerAssociationTypeEnum = Field(
        AnswerAssociationTypeEnum.positive, # Default to positive
        description="Defines how the question's answer outcome relates to the course skill."
    )
    # Course-specific feedback overrides or additions, based on the score for THIS question
    # when answered in the context of THIS course.
    feedbacks_based_on_score: Optional[List[ScoreFeedbackItem]] = Field(
        None, 
        description="Course-specific feedback based on the question's score for this association."
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
        arbitrary_types_allowed=True # For PyObjectId
    )

class QcaCreate(QcaBase):
    pass

class QcaUpdate(BaseModel):
    # Only association type and feedback can be updated. Question/Course link is immutable for an association.
    # To change question/course, delete and create a new association.
    answer_association_type: Optional[AnswerAssociationTypeEnum] = None
    feedbacks_based_on_score: Optional[List[ScoreFeedbackItem]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid'
    )

class QcaInDB(QcaBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id") 

class QcaOut(QcaBase): # Output model
    id: str # String ID

    # Optional: Include populated Question and Course details for convenience
    # To do this, you'd add fields here and resolve them in the router.
    # For now, keeping it simple with just IDs.
    # question: Optional[QuestionOut] = None 
    # course: Optional[CourseOut] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
