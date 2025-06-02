// File: ui/src/types/surveyAttemptTypes.ts
import type { SurveyQuestionDetailFE, OutcomeCategoryEnumFE } from './surveyTypes';

// Payload for submitting a single answer or multiple answers
// Corresponds to backend's StudentAnswerPayload
export interface StudentAnswerPayloadFE {
  qca_id: string;
  question_id: string;
  answer_value: any; // Can be string, string[], number
}

// How a student's answer is represented after saving/fetching
// Corresponds to backend's StudentAnswerOut
export interface StudentAnswerFE extends StudentAnswerPayloadFE {
  id: string;
  survey_attempt_id: string;
  student_id: string;
  answered_at: string; // ISO date string
  score_achieved?: number | null;
}

// Output when starting a survey attempt
// Corresponds to backend's SurveyAttemptStartOut
export interface SurveyAttemptStartFE {
  attempt_id: string;
  survey_id: string;
  student_id: string;
  started_at: string; // ISO date string
  questions: SurveyQuestionDetailFE[];
}

// Base for survey attempt data
// Corresponds to backend's SurveyAttemptBase
interface SurveyAttemptBaseFE {
  student_id: string;
  survey_id: string;
  is_submitted: boolean;
  started_at: string; // ISO date string
  submitted_at?: string | null; // ISO date string
  course_scores: Record<string, number>; // course_id (string) -> score
  course_feedback: Record<string, string>; // course_id (string) -> feedback string
  detailed_feedback: Record<string, string[]>; // course_id (string) -> list of feedback strings
  overall_survey_feedback?: string | null;
  course_outcome_categorization: Record<string, OutcomeCategoryEnumFE>; // course_id (string) -> outcome
  // ADDED max score fields, assuming they come with the attempt result (populated from Survey)
  max_scores_per_course?: Record<string, number> | null;
  max_overall_survey_score?: number | null;
}

// For listing user's attempts (student view) or attempts for a survey (teacher view)
// Corresponds to backend's SurveyAttemptOut (without answers by default)
export interface SurveyAttemptListItemFE extends SurveyAttemptBaseFE {
  id: string;
  survey_title?: string; // For student's "My Attempts" page
  // For teacher's view of attempts on a survey, student info is crucial
  student_display_name?: string; // Ideally provided by backend for /by-survey/ endpoint
  // max_scores_per_course and max_overall_survey_score are inherited
}

// For displaying full results of a submitted survey
// Corresponds to backend's SurveyAttemptResultOut (includes answers)
export interface SurveyAttemptResultFE extends SurveyAttemptBaseFE {
  id: string;
  answers: StudentAnswerFE[];
  student_display_name?: string; // Add here too, if backend can provide it for results page
  // max_scores_per_course and max_overall_survey_score are inherited
}
