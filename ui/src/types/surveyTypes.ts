// File: ui/src/types/surveyTypes.ts
// Corresponds to backend's AnswerTypeEnum
export enum AnswerTypeEnumFE { 
  MULTIPLE_CHOICE = "multiple_choice",
  MULTIPLE_SELECT = "multiple_select",
  INPUT = "input",
  RANGE = "range",
}

// Corresponds to backend's FeedbackComparisonEnum
export enum FeedbackComparisonEnumFE {
  LT = "lt",
  LTE = "lte",
  GT = "gt",
  GTE = "gte",
  EQ = "eq",
  NEQ = "neq",
}

// Corresponds to backend's ScoreFeedbackItem
export interface ScoreFeedbackItemFE {
  score_value: number;
  comparison: FeedbackComparisonEnumFE;
  feedback: string;
}

// Corresponds to backend's OutcomeCategoryEnum
export enum OutcomeCategoryEnumFE {
  RECOMMENDED = "RECOMMENDED_TO_TAKE_COURSE",
  ELIGIBLE_FOR_ERPL = "ELIGIBLE_FOR_ERPL",
  NOT_SUITABLE = "NOT_SUITABLE_FOR_COURSE",
  UNDEFINED = "UNDEFINED",
}

// Corresponds to backend's OutcomeThresholdItem
export interface OutcomeThresholdItemFE {
  score_value: number;
  comparison: FeedbackComparisonEnumFE;
  outcome: OutcomeCategoryEnumFE;
}

// Corresponds to backend's SurveyQuestionDetail
export interface SurveyQuestionDetailFE {
  question_id: string;
  qca_id: string; 
  course_id: string;
  title: string;
  details?: string | null;
  answer_type: AnswerTypeEnumFE;
  answer_options?: Record<string, any> | null;
}

// For listing surveys - a summary view
export interface SurveySummaryListItemFE {
  id: string;
  title: string;
  description?: string | null;
  course_ids: string[];
  is_published: boolean;
  created_by: string;
  created_at: string; 
  updated_at: string; 
  max_scores_per_course?: Record<string, number> | null; // ADDED: Key is course_id string
  max_overall_survey_score?: number | null;             // ADDED
}

// For taking a survey or editing - detailed view
export interface SurveyFE extends SurveySummaryListItemFE { 
  questions?: SurveyQuestionDetailFE[]; 
  course_skill_total_score_thresholds?: Record<string, ScoreFeedbackItemFE[]> | null; 
  course_outcome_thresholds?: Record<string, OutcomeThresholdItemFE[]> | null;
  // max_scores_per_course and max_overall_survey_score are inherited
}

// For creating a survey
export interface SurveyCreateFE {
  title: string;
  description?: string | null;
  course_ids: string[]; 
  is_published: boolean;
  course_skill_total_score_thresholds?: Record<string, ScoreFeedbackItemFE[]>; 
  course_outcome_thresholds?: Record<string, OutcomeThresholdItemFE[]>;
  // Note: max scores are typically calculated by backend, not sent on create
}

// For updating a survey
export interface SurveyUpdateFE {
  title?: string;
  description?: string | null;
  course_ids?: string[];
  is_published?: boolean;
  course_skill_total_score_thresholds?: Record<string, ScoreFeedbackItemFE[]>;
  course_outcome_thresholds?: Record<string, OutcomeThresholdItemFE[]>;
  // Note: max scores are typically recalculated by backend on update
}

export type SurveyForTakingFE = SurveyFE;
