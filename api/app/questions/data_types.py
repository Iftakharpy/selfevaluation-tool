# FilePath: api/app/questions/data_types.py
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict, model_validator, ValidationInfo # Ensure ValidationInfo is imported
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

# Ensure ScoreFeedbackItem also has arbitrary_types_allowed if it ever uses custom non-Pydantic types
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
    scoring_rules: Dict[str, Any]
    default_feedbacks_on_score: Optional[List[ScoreFeedbackItem]] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
        arbitrary_types_allowed=True # Crucial for models that might contain PyObjectId or other custom types
    )

    @model_validator(mode='after')
    def check_options_and_rules_consistency(self) -> QuestionBase:
        # ... (validator code as corrected before) ...
        answer_type = self.answer_type
        options = self.answer_options
        rules = self.scoring_rules

        if answer_type == AnswerTypeEnum.multiple_choice or answer_type == AnswerTypeEnum.multiple_select:
            if not options or not isinstance(options, dict):
                raise ValueError(f"answer_options must be a non-empty dictionary for {answer_type.value}")
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in options.items()):
                raise ValueError(f"answer_options for {answer_type.value} must be Dict[str, str] (option_key: option_text)")

            if answer_type == AnswerTypeEnum.multiple_choice:
                has_option_scores = "option_scores" in rules and isinstance(rules.get("option_scores"), dict)
                has_correct_key = "correct_option_key" in rules and isinstance(rules.get("correct_option_key"), str)
                if not (has_option_scores or has_correct_key):
                    raise ValueError("scoring_rules for multiple_choice must define 'option_scores' or 'correct_option_key'")
                if has_correct_key and rules["correct_option_key"] not in options:
                    raise ValueError(f"correct_option_key '{rules['correct_option_key']}' not found in answer_options")
                if has_option_scores:
                    for opt_key in rules["option_scores"]:
                        if opt_key not in options:
                            raise ValueError(f"Key '{opt_key}' in option_scores not found in answer_options")
            
            elif answer_type == AnswerTypeEnum.multiple_select:
                has_option_scores = "option_scores" in rules and isinstance(rules.get("option_scores"), dict)
                has_correct_keys = "correct_option_keys" in rules and isinstance(rules.get("correct_option_keys"), list)
                
                if not (has_option_scores or has_correct_keys):
                    raise ValueError("scoring_rules for multiple_select needs 'option_scores' or 'correct_option_keys'")
                if has_correct_keys:
                    for key in rules["correct_option_keys"]:
                        if key not in options:
                            raise ValueError(f"Key '{key}' in correct_option_keys not found in answer_options")

        elif answer_type == AnswerTypeEnum.range:
            if not options or not isinstance(options, dict):
                raise ValueError("answer_options must be a dictionary for range type")
            if not all(k in options for k in ["min", "max"]):
                raise ValueError("answer_options for range must include 'min' and 'max' keys")
            min_val, max_val = options.get("min"), options.get("max")
            if not (isinstance(min_val, (int, float)) and isinstance(max_val, (int, float))):
                 raise ValueError("'min' and 'max' in answer_options for range must be numbers")
            if min_val >= max_val: # type: ignore
                raise ValueError("'min' must be less than 'max' for range options")
        
        elif answer_type == AnswerTypeEnum.input:
            if options is not None and not isinstance(options, dict):
                raise ValueError("answer_options for input, if provided, must be a dictionary.")
            if "expected_answers" not in rules or not isinstance(rules.get("expected_answers"), list):
                raise ValueError("scoring_rules for input type must contain 'expected_answers' list.")

        return self

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255) # min_length was 3, was it 5 before?
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
        arbitrary_types_allowed=True # Good to have here too
    )