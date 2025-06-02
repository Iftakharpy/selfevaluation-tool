# api/app/questions/data_types.py
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict, model_validator, ValidationInfo
from typing import Optional, Annotated, List, Dict, Any
from bson import ObjectId
from enum import Enum

from app.users.data_types import PyObjectId 
from pydantic.functional_validators import BeforeValidator

class AnswerTypeEnum(str, Enum):
    multiple_choice = "multiple_choice"
    multiple_select = "multiple_select"
    input = "input"
    range = "range"

class FeedbackComparisonEnum(str, Enum):
    lt = "lt"; lte = "lte"; gt = "gt"; gte = "gte"; eq = "eq"; neq = "neq"

class ScoreFeedbackItem(BaseModel):
    score_value: float = Field(..., description="The score threshold value.")
    comparison: FeedbackComparisonEnum
    feedback: str
    model_config = ConfigDict(populate_by_name=True, extra='forbid', arbitrary_types_allowed=True)


class QuestionBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    details: Optional[str] = Field(None, max_length=2000)
    answer_type: AnswerTypeEnum
    answer_options: Optional[Dict[str, Any]] = None
    scoring_rules: Dict[str, Any] = Field(
        ...,
        description="Rules for scoring the question, aiming for a 0-10 point scale per question. The system will normalize/cap scores.",
        examples=[ # List of example dictionaries
            {"correct_option_key": "a", "score_if_correct": 10, "score_if_incorrect": 0}, 
            {"option_scores": {"a": 10, "b": 5, "c": 0}}, # Example for multiple_choice/multiple_select
            {"expected_answers": [{"text": "OpenAI", "score": 10, "case_sensitive": False}], "default_incorrect_score": 0}, # Example for input
            {"target_value": 7, "score_at_target": 10, "score_per_deviation_unit": -1} # Example for range
        ]
    )
    default_feedbacks_on_score: Optional[List[ScoreFeedbackItem]] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
        arbitrary_types_allowed=True 
    )

    @model_validator(mode='after')
    def check_options_and_rules_consistency(self) -> QuestionBase:
        answer_type = self.answer_type
        options = self.answer_options
        rules = self.scoring_rules

        if answer_type == AnswerTypeEnum.multiple_choice or answer_type == AnswerTypeEnum.multiple_select:
            if not options or not isinstance(options, dict):
                raise ValueError(f"answer_options must be a non-empty dictionary for {answer_type.value}")
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in options.items()): # type: ignore
                raise ValueError(f"answer_options for {answer_type.value} must be Dict[str, str] (option_key: option_text)")

            if answer_type == AnswerTypeEnum.multiple_choice:
                has_option_scores = "option_scores" in rules and isinstance(rules.get("option_scores"), dict)
                has_correct_key = "correct_option_key" in rules and isinstance(rules.get("correct_option_key"), str)
                if not (has_option_scores or has_correct_key):
                    raise ValueError("scoring_rules for multiple_choice must define 'option_scores' (e.g. {'a':10,'b':0}) or 'correct_option_key' (e.g. 'a' for a simple 10/0 score).")
                if has_correct_key and rules["correct_option_key"] not in options: # type: ignore
                    raise ValueError(f"correct_option_key '{rules['correct_option_key']}' not found in answer_options")
                if has_option_scores:
                    for opt_key in rules["option_scores"]: # type: ignore
                        if opt_key not in options: # type: ignore
                            raise ValueError(f"Key '{opt_key}' in option_scores not found in answer_options")
            
            elif answer_type == AnswerTypeEnum.multiple_select:
                has_option_scores = "option_scores" in rules and isinstance(rules.get("option_scores"), dict)
                has_correct_keys = "correct_option_keys" in rules and isinstance(rules.get("correct_option_keys"), list)
                
                if not (has_option_scores or has_correct_keys):
                    raise ValueError("scoring_rules for multiple_select needs 'option_scores' (e.g. {'a':5,'b':5}) or 'correct_option_keys' (e.g. ['a','b'] for distributed score).")
                if has_correct_keys:
                    for key in rules["correct_option_keys"]: # type: ignore
                        if key not in options: # type: ignore
                            raise ValueError(f"Key '{key}' in correct_option_keys not found in answer_options")

        elif answer_type == AnswerTypeEnum.range:
            if not options or not isinstance(options, dict):
                raise ValueError("answer_options must be a dictionary for range type")
            if not all(k in options for k in ["min", "max"]): # type: ignore
                raise ValueError("answer_options for range must include 'min' and 'max' keys")
            min_val, max_val = options.get("min"), options.get("max") # type: ignore
            if not (isinstance(min_val, (int, float)) and isinstance(max_val, (int, float))):
                 raise ValueError("'min' and 'max' in answer_options for range must be numbers")
            if min_val >= max_val: 
                raise ValueError("'min' must be less than 'max' for range options")
        
        elif answer_type == AnswerTypeEnum.input:
            if options is not None and not isinstance(options, dict): # e.g. {"max_length": 100}
                pass # Optional options are fine
            if "expected_answers" not in rules or not isinstance(rules.get("expected_answers"), list):
                raise ValueError("scoring_rules for input type must contain 'expected_answers' list (e.g., [{'text':'ans', 'score':10}]).")
            # Ensure default_incorrect_score if expected_answers list is empty but present
            if "expected_answers" in rules and not rules.get("expected_answers") and "default_incorrect_score" not in rules:
                 raise ValueError("If 'expected_answers' is an empty list for input type, 'default_incorrect_score' must be provided in scoring_rules.")

        return self

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    details: Optional[str] = Field(None, max_length=2000)
    answer_type: Optional[AnswerTypeEnum] = None
    answer_options: Optional[Dict[str, Any]] = None
    scoring_rules: Optional[Dict[str, Any]] = None
    default_feedbacks_on_score: Optional[List[ScoreFeedbackItem]] = None
    model_config = ConfigDict(populate_by_name=True, extra='forbid')

class QuestionInDB(QuestionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

class QuestionOut(QuestionBase): 
    id: str 
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
