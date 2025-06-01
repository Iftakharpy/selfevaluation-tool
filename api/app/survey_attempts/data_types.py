from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.users.data_types import PyObjectId
from app.surveys.data_types import SurveyQuestionDetail # For context when starting survey
from datetime import datetime, UTC # Ensure UTC is imported

class StudentAnswerPayload(BaseModel):
    """Payload for a student submitting a single answer."""
    qca_id: PyObjectId      # QuestionCourseAssociation ID
    question_id: PyObjectId # The actual Question ID
    answer_value: Any       # The student's actual answer (type depends on question)

class StudentAnswerInDB(StudentAnswerPayload):
    """How a student's answer is stored in the database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    survey_attempt_id: PyObjectId
    student_id: PyObjectId 
    answered_at: datetime = Field(default_factory=lambda: datetime.now(UTC)) # Using UTC
    score_achieved: Optional[float] = None # Populated upon survey submission

class StudentAnswerOut(StudentAnswerInDB):
    id: str
    qca_id: str
    question_id: str
    survey_attempt_id: str
    student_id: str
    # score_achieved will be present if calculated
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SurveyAttemptBase(BaseModel):
    student_id: PyObjectId
    survey_id: PyObjectId
    is_submitted: bool = Field(False)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC)) # Using UTC
    submitted_at: Optional[datetime] = None
    course_scores: Dict[str, float] = Field(default_factory=dict, description="Final scores per course ID (str representation of PyObjectId).")
    # Overall feedback per course (summary string)
    course_feedback: Dict[str, str] = Field(default_factory=dict, description="Overall feedback per course ID (str representation of PyObjectId).")
    # Detailed feedback items per course (list of strings)
    detailed_feedback: Dict[str, List[str]] = Field(default_factory=dict, description="List of detailed feedback messages per course ID (str representation of PyObjectId).")
    # A single overall feedback message for the entire survey
    overall_survey_feedback: Optional[str] = Field(None, description="A single overall feedback for the entire survey based on performance.")
    
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
    # Inherits fields from SurveyAttemptOut; 
    # course_scores, course_feedback, detailed_feedback, overall_survey_feedback will be populated.
    pass

class SubmitAnswersRequest(BaseModel):
    """Request payload for submitting multiple answers at once."""
    answers: List[StudentAnswerPayload]
