import type { AnswerTypeEnumFE, ScoreFeedbackItemFE } from './surveyTypes'; // Re-use existing enums/types

// For displaying a question in a list or for basic viewing
export interface QuestionListItemFE {
  id: string;
  title: string;
  answer_type: AnswerTypeEnumFE;
  details?: string | null;
}

// For creating or editing a question (full detail)
// Corresponds to backend's QuestionBase/QuestionCreate/QuestionUpdate
export interface QuestionFE {
  id?: string; // Optional for create, present for update/view
  title: string;
  details?: string | null;
  answer_type: AnswerTypeEnumFE;
  answer_options?: Record<string, any> | null; // E.g., { "a": "Opt A"} or {"min": 1, "max": 5}
  scoring_rules: Record<string, any>; // E.g., {"correct_option_key": "a"} or {"target_value": 3}
  default_feedbacks_on_score?: ScoreFeedbackItemFE[] | null;
}

export interface QuestionCreateFE extends Omit<QuestionFE, 'id'> {}
export interface QuestionUpdateFE extends Partial<Omit<QuestionFE, 'id'>> {}