# api/app/survey_attempts/data_types.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.users.data_types import PyObjectId
from app.surveys.data_types import SurveyQuestionDetail, OutcomeCategoryEnum
from datetime import datetime, UTC 

class StudentAnswerPayload(BaseModel):
    qca_id: PyObjectId      
    question_id: PyObjectId 
    answer_value: Any       

class StudentAnswerInDB(StudentAnswerPayload):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    survey_attempt_id: PyObjectId
    student_id: PyObjectId 
    answered_at: datetime = Field(default_factory=lambda: datetime.now(UTC)) 
    score_achieved: Optional[float] = None 

class StudentAnswerOut(StudentAnswerInDB):
    id: str
    qca_id: str
    question_id: str
    survey_attempt_id: str
    student_id: str
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SurveyAttemptBase(BaseModel):
    student_id: PyObjectId
    survey_id: PyObjectId
    is_submitted: bool = Field(False)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC)) 
    submitted_at: Optional[datetime] = None
    course_scores: Dict[str, float] = Field(default_factory=dict, description="Final scores per course ID.")
    course_feedback: Dict[str, str] = Field(default_factory=dict, description="Overall feedback per course ID.")
    detailed_feedback: Dict[str, List[str]] = Field(default_factory=dict, description="Detailed feedback messages per course ID.")
    overall_survey_feedback: Optional[str] = Field(None, description="Overall feedback for the survey.")
    course_outcome_categorization: Dict[str, OutcomeCategoryEnum] = Field(default_factory=dict)
    
    max_scores_per_course: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Maximum possible score for each course in this survey. Key is course_id (str)."
    )
    max_overall_survey_score: Optional[float] = Field(
        None,
        description="Overall maximum possible score for this survey."
    )
    survey_title: Optional[str] = None # ADDED FIELD FOR SURVEY TITLE
    survey_description: Optional[str] = None # ADDED FIELD FOR SURVEY DESCRIPTION
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class SurveyAttemptCreateRequest(BaseModel):
    survey_id: PyObjectId

class SurveyAttemptInDB(SurveyAttemptBase): 
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

class SurveyAttemptStartOut(BaseModel):
    attempt_id: str
    survey_id: str
    student_id: str
    started_at: datetime
    questions: List[SurveyQuestionDetail] 

class SurveyAttemptOut(SurveyAttemptBase): 
    id: str
    student_id: str 
    survey_id: str  
    answers: Optional[List[StudentAnswerOut]] = None 
    student_display_name: Optional[str] = None 
    # survey_title and survey_description will be inherited from SurveyAttemptBase
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SurveyAttemptResultOut(SurveyAttemptOut): 
    pass

class SubmitAnswersRequest(BaseModel):
    answers: List[StudentAnswerPayload]