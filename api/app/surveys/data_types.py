from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.users.data_types import PyObjectId
from app.questions.data_types import AnswerTypeEnum, ScoreFeedbackItem, FeedbackComparisonEnum # MODIFIED: Imported FeedbackComparisonEnum
from datetime import datetime, UTC
from enum import Enum


class OutcomeCategoryEnum(str, Enum):
    RECOMMENDED = "RECOMMENDED_TO_TAKE_COURSE"
    ELIGIBLE_FOR_ERPL = "ELIGIBLE_FOR_ERPL"
    NOT_SUITABLE = "NOT_SUITABLE_FOR_COURSE"
    UNDEFINED = "UNDEFINED" # Fallback category

class OutcomeThresholdItem(BaseModel):
    score_value: float = Field(..., description="The score threshold value.")
    comparison: FeedbackComparisonEnum
    outcome: OutcomeCategoryEnum
    model_config = ConfigDict(populate_by_name=True, extra='forbid', arbitrary_types_allowed=True)

class SurveyQuestionDetail(BaseModel):
    """Detailed information about a question as part of a survey."""
    question_id: str
    qca_id: str
    course_id: str
    title: str
    details: Optional[str] = None
    answer_type: AnswerTypeEnum
    answer_options: Optional[Dict[str, Any]] = None

class SurveyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, examples=["Programming Pre-assessment"])
    description: Optional[str] = Field(None, max_length=1000, examples=["Assesses readiness for programming courses."])
    course_ids: List[PyObjectId] = Field(..., description="List of Course IDs associated with this survey.")
    is_published: bool = Field(False, description="Whether the survey is available for students to take.")
    
    course_skill_total_score_thresholds: Optional[Dict[str, List[ScoreFeedbackItem]]] = Field(
        default_factory=dict, 
        description="Feedback rules based on total scores for each course in the survey. Key is course_id (str)."
    )
    
    course_outcome_thresholds: Optional[Dict[str, List[OutcomeThresholdItem]]] = Field(
        default_factory=dict,
        description="Outcome categorization rules based on total scores for each course. Key is course_id (str)."
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "title": "Pre-assessment for Programming Basics",
                "description": "This survey helps assess your readiness for programming courses.",
                "course_ids": ["60c72b2f9b1e8b001c8e4d8a", "60c72b2f9b1e8b001c8e4d8b"],
                "is_published": False,
                "course_skill_total_score_thresholds": {
                    "60c72b2f9b1e8b001c8e4d8a": [ 
                        {"score_value": 10, "comparison": "lt", "feedback": "Needs significant review for this course."},
                        {"score_value": 20, "comparison": "gte", "feedback": "Good grasp of concepts for this course."}
                    ]
                },
                "course_outcome_thresholds": {
                    "60c72b2f9b1e8b001c8e4d8a": [
                        {"score_value": 5, "comparison": "lt", "outcome": "NOT_SUITABLE_FOR_COURSE"},
                        {"score_value": 15, "comparison": "lt", "outcome": "RECOMMENDED_TO_TAKE_COURSE"},
                        {"score_value": 15, "comparison": "gte", "outcome": "ELIGIBLE_FOR_ERPL"}
                    ]
                }
            }
        }
    )

class SurveyCreate(SurveyBase):
    pass

class SurveyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    course_ids: Optional[List[PyObjectId]] = None
    is_published: Optional[bool] = None
    course_skill_total_score_thresholds: Optional[Dict[str, List[ScoreFeedbackItem]]] = None
    course_outcome_thresholds: Optional[Dict[str, List[OutcomeThresholdItem]]] = None


    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class SurveyInDB(SurveyBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class SurveyOut(SurveyBase):
    id: str
    created_by: str
    course_ids: List[str]
    created_at: datetime
    updated_at: datetime
    
    questions: Optional[List[SurveyQuestionDetail]] = Field(None, description="Detailed questions for this survey.")

    course_skill_total_score_thresholds: Optional[Dict[str, List[ScoreFeedbackItem]]]
    course_outcome_thresholds: Optional[Dict[str, List[OutcomeThresholdItem]]]

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )