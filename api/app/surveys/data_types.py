# FilePath: C:\Users\iftak\Desktop\jamk\2025 Spring\narsus-self-evaluation-tool\api\app\surveys\data_types.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.users.data_types import PyObjectId 
from app.questions.data_types import AnswerTypeEnum, ScoreFeedbackItem # MODIFIED: Imported ScoreFeedbackItem
from datetime import datetime, UTC

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
    
    # MODIFIED: Added field for survey-level feedback rules based on course total scores
    course_skill_total_score_thresholds: Optional[Dict[str, List[ScoreFeedbackItem]]] = Field(
        default_factory=dict, # Use default_factory for mutable defaults
        description="Feedback rules based on total scores for each course in the survey. Key is course_id (str)."
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
                    "60c72b2f9b1e8b001c8e4d8a": [ # course_id
                        {"score_value": 10, "comparison": "lt", "feedback": "Needs significant review for this course."},
                        {"score_value": 20, "comparison": "gte", "feedback": "Good grasp of concepts for this course."}
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
    # MODIFIED: Added field for survey-level feedback rules update
    course_skill_total_score_thresholds: Optional[Dict[str, List[ScoreFeedbackItem]]] = None

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

    # Output model for course_skill_total_score_thresholds will have string keys
    course_skill_total_score_thresholds: Optional[Dict[str, List[ScoreFeedbackItem]]] 

    model_config = ConfigDict(
        from_attributes=True, 
        populate_by_name=True
    )
