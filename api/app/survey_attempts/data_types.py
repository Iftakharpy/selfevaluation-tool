from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.users.data_types import PyObjectId
from app.surveys.data_types import SurveyQuestionDetail, OutcomeCategoryEnum # MODIFIED: Added OutcomeCategoryEnum
from datetime import datetime, UTC 

class StudentAnswerPayload(BaseModel):
    """Payload for a student submitting a single answer."""
    qca_id: PyObjectId      
    question_id: PyObjectId 
    answer_value: Any       

class StudentAnswerInDB(StudentAnswerPayload):
    """How a student's answer is stored in the database."""
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
    course_scores: Dict[str, float] = Field(default_factory=dict, description="Final scores per course ID (str representation of PyObjectId).")
    course_feedback: Dict[str, str] = Field(default_factory=dict, description="Overall feedback per course ID (str representation of PyObjectId).")
    detailed_feedback: Dict[str, List[str]] = Field(default_factory=dict, description="List of detailed feedback messages per course ID (str representation of PyObjectId).")
    overall_survey_feedback: Optional[str] = Field(None, description="A single overall feedback for the entire survey based on performance.")
    
    # MODIFIED: Added course_outcome_categorization field
    course_outcome_categorization: Dict[str, OutcomeCategoryEnum] = Field(
        default_factory=dict, 
        description="Final outcome category per course ID (str representation of PyObjectId)."
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class SurveyAttemptCreateRequest(BaseModel):
    """Used when a student requests to start a survey."""
    survey_id: PyObjectId

class SurveyAttemptInDB(SurveyAttemptBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

class SurveyAttemptStartOut(BaseModel):
    """Output when starting a survey or getting an ongoing attempt's question list."""
    attempt_id: str
    survey_id: str
    student_id: str
    started_at: datetime
    questions: List[SurveyQuestionDetail] 

class SurveyAttemptOut(SurveyAttemptBase):
    """General output for a survey attempt, potentially including answers."""
    id: str
    student_id: str
    survey_id: str
    answers: Optional[List[StudentAnswerOut]] = None 
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SurveyAttemptResultOut(SurveyAttemptOut):
    """Output when a survey is submitted and results are shown (includes scores and feedback)."""
    pass

class SubmitAnswersRequest(BaseModel):
    """Request payload for submitting multiple answers at once."""
    answers: List[StudentAnswerPayload]