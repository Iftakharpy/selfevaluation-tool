import pytest
from typing import Dict, Any

# Function to be tested (imagine it's imported or defined here for testing)
# For a real test, you'd import it: from app.survey_attempts.router import calculate_score_for_answer
# For this simulation, I'll define a simplified version or assume it's accessible.
# We'll use the actual one from the provided file structure context.
from app.survey_attempts.router import calculate_score_for_answer
from app.questions.data_types import AnswerTypeEnum
from app.core.settings import STANDARD_QUESTION_MAX_SCORE # Should be 10.0

# --- Test Cases ---

@pytest.mark.asyncio
@pytest.mark.parametrize("question_config, answer, expected_score", [
    # Multiple Choice - Correct Option Key
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"correct_option_key": "a", "score_if_correct": 5.0, "score_if_incorrect": 0.5}}, "a", 5.0),
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"correct_option_key": "a", "score_if_correct": 5.0, "score_if_incorrect": 0.5}}, "b", 0.5),
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"correct_option_key": "a", "score_if_correct": 12.0}}, "a", STANDARD_QUESTION_MAX_SCORE), # Test capping
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"correct_option_key": "a"}}, "a", STANDARD_QUESTION_MAX_SCORE), # Default score_if_correct
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"correct_option_key": "a"}}, "b", 0.0), # Default score_if_incorrect

    # Multiple Choice - Option Scores
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"option_scores": {"a": 7.0, "b": 2.0, "c": 0.0}}}, "a", 7.0),
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"option_scores": {"a": 7.0, "b": 2.0, "c": 0.0}}}, "b", 2.0),
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"option_scores": {"a": 15.0, "b": 2.0}}}, "a", STANDARD_QUESTION_MAX_SCORE), # Capping
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"option_scores": {"a": -2.0, "b": 2.0}}}, "a", 0.0), # Min score 0

    # Multiple Select - Correct Option Keys (score_per_correct, penalty_per_incorrect)
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "answer_options": {"a": "A", "b": "B", "c":"C", "d":"D"}, "scoring_rules": {"correct_option_keys": ["a", "b"], "score_per_correct": 3.0, "penalty_per_incorrect": -1.0}}, ["a", "b"], 6.0),
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "answer_options": {"a": "A", "b": "B", "c":"C", "d":"D"}, "scoring_rules": {"correct_option_keys": ["a", "b"], "score_per_correct": 3.0, "penalty_per_incorrect": -1.0}}, ["a"], 3.0),
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "answer_options": {"a": "A", "b": "B", "c":"C", "d":"D"}, "scoring_rules": {"correct_option_keys": ["a", "b"], "score_per_correct": 3.0, "penalty_per_incorrect": -1.0}}, ["a", "c"], 2.0), # 3 for a, -1 for c
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "answer_options": {"a": "A", "b": "B", "c":"C", "d":"D"}, "scoring_rules": {"correct_option_keys": ["a", "b"], "score_per_correct": 3.0, "penalty_per_incorrect": -1.0}}, ["c", "d"], 0.0), # -1 for c, -1 for d -> -2, capped to 0
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "answer_options": {"a": "A", "b": "B"}, "scoring_rules": {"correct_option_keys": ["a", "b"], "score_per_correct": 6.0}}, ["a", "b"], STANDARD_QUESTION_MAX_SCORE), # Capping (6+6=12)
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "answer_options": {"a": "A", "b": "B", "c":"C"}, "scoring_rules": {"correct_option_keys": ["a", "b"]}}, ["a","b","c"], (STANDARD_QUESTION_MAX_SCORE / 2) * 2 + 0.0), # Default score_per_correct, no penalty for undefined c

    # Multiple Select - Option Scores
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "scoring_rules": {"option_scores": {"a": 4.0, "b": 3.0, "c": -1.0}}}, ["a", "b"], 7.0),
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "scoring_rules": {"option_scores": {"a": 4.0, "b": 3.0, "c": -1.0}}}, ["a", "c"], 3.0), # 4 - 1
    ({"answer_type": AnswerTypeEnum.multiple_select.value, "scoring_rules": {"option_scores": {"a": 8.0, "b": 7.0}}}, ["a", "b"], STANDARD_QUESTION_MAX_SCORE), # Capping (8+7=15)

    # Input - Expected Answers
    ({"answer_type": AnswerTypeEnum.input.value, "scoring_rules": {"expected_answers": [{"text": "Test", "score": 8.0, "case_sensitive": False}], "default_incorrect_score": 0.0}}, "test", 8.0),
    ({"answer_type": AnswerTypeEnum.input.value, "scoring_rules": {"expected_answers": [{"text": "Test", "score": 8.0, "case_sensitive": True}], "default_incorrect_score": 0.0}}, "test", 0.0),
    ({"answer_type": AnswerTypeEnum.input.value, "scoring_rules": {"expected_answers": [{"text": "Test", "score": 8.0, "case_sensitive": True}], "default_incorrect_score": 0.0}}, "Test", 8.0),
    ({"answer_type": AnswerTypeEnum.input.value, "scoring_rules": {"expected_answers": [{"text": "Test", "score": 12.0}], "default_incorrect_score": 0.0}}, "test", STANDARD_QUESTION_MAX_SCORE), # Capping
    ({"answer_type": AnswerTypeEnum.input.value, "scoring_rules": {"expected_answers": [{"text": "Correct1", "score": 5.0}, {"text": "Correct2", "score": 6.0}], "default_incorrect_score": 1.0}}, "wrong", 1.0),
    ({"answer_type": AnswerTypeEnum.input.value, "scoring_rules": {"expected_answers": [], "default_incorrect_score": 1.5}}, "anything", 1.5),

    # Range
    ({"answer_type": AnswerTypeEnum.range.value, "answer_options": {"min": 0, "max": 10}, "scoring_rules": {"target_value": 5, "score_at_target": 10, "score_per_deviation_unit": -1}}, 5, 10.0),
    ({"answer_type": AnswerTypeEnum.range.value, "answer_options": {"min": 0, "max": 10}, "scoring_rules": {"target_value": 5, "score_at_target": 10, "score_per_deviation_unit": -1}}, 7, 8.0), # 10 + (2 * -1)
    ({"answer_type": AnswerTypeEnum.range.value, "answer_options": {"min": 0, "max": 10}, "scoring_rules": {"target_value": 5, "score_at_target": 10, "score_per_deviation_unit": -1}}, 0, 5.0), # 10 + (5 * -1)
    ({"answer_type": AnswerTypeEnum.range.value, "answer_options": {"min": 0, "max": 10}, "scoring_rules": {"target_value": 5, "score_at_target": 10, "score_per_deviation_unit": -3}}, 7, 4.0), # 10 + (2 * -3)
    ({"answer_type": AnswerTypeEnum.range.value, "answer_options": {"min": 0, "max": 10}, "scoring_rules": {"target_value": 5, "score_at_target": 10, "score_per_deviation_unit": -3}}, 8, 1.0), # 10 + (3 * -3) = 1
    ({"answer_type": AnswerTypeEnum.range.value, "answer_options": {"min": 0, "max": 10}, "scoring_rules": {"target_value": 5, "score_at_target": 10, "score_per_deviation_unit": -3}}, 9, 0.0), # 10 + (4 * -3) = -2 -> 0
    ({"answer_type": AnswerTypeEnum.range.value, "answer_options": {"min": 0, "max": 10}, "scoring_rules": {"target_value": 5, "score_at_target": 15, "score_per_deviation_unit": -1}}, 5, STANDARD_QUESTION_MAX_SCORE), # Capping score_at_target

    # Unanswered
    ({"answer_type": AnswerTypeEnum.multiple_choice.value, "scoring_rules": {"correct_option_key": "a", "score_if_unanswered": 1.0}}, None, 1.0),
    ({"answer_type": AnswerTypeEnum.input.value, "scoring_rules": {"expected_answers": [], "default_incorrect_score": 0.0, "score_if_unanswered": 0.5}}, None, 0.5),
    ({"answer_type": AnswerTypeEnum.input.value, "scoring_rules": {"score_if_unanswered": 12.0}}, None, STANDARD_QUESTION_MAX_SCORE), # Cap unanswered score
])
async def test_calculate_score_for_answer_various_scenarios(question_config: Dict[str, Any], answer: Any, expected_score: float):
    # Add a default title if not present, as it's used in error messages but not for logic
    if "title" not in question_config:
        question_config["title"] = "Test Question"
    
    score = await calculate_score_for_answer(question_config, answer)
    assert score == expected_score, f"Failed for Q type: {question_config['answer_type']}, Answer: {answer}"
