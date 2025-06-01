// Corresponds to backend's AnswerTypeEnum
export enum AnswerTypeEnumFE { // Added FE suffix to avoid potential name clashes if importing from backend types directly later
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
  qca_id: string; // QuestionCourseAssociation ID
  course_id: string;
  title: string;
  details?: string | null;
  answer_type: AnswerTypeEnumFE;
  answer_options?: Record<string, any> | null; // e.g., { "a": "Option A", "b": "Option B" } or { "min": 0, "max": 10 }
}

// For listing surveys - a summary view (maps to backend's SurveyOut, potentially without questions)
export interface SurveySummaryListItemFE {
  id: string;
  title: string;
  description?: string | null;
  course_ids: string[];
  is_published: boolean;
  created_by: string;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  // อาจจะเพิ่มจำนวนคำถามหรือ course names ที่ resolve แล้วถ้า API ส่งมา
}

// For taking a survey - detailed view (maps to backend's SurveyOut with include_questions=true)
export interface SurveyForTakingFE extends SurveySummaryListItemFE {
  questions: SurveyQuestionDetailFE[]; // Included when fetching for taking a survey
  course_skill_total_score_thresholds?: Record<string, ScoreFeedbackItemFE[]> | null;
  course_outcome_thresholds?: Record<string, OutcomeThresholdItemFE[]> | null;
}