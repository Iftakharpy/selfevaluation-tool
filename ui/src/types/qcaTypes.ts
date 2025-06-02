import type { ScoreFeedbackItemFE } from './surveyTypes';

// Corresponds to backend's AnswerAssociationTypeEnum
export enum AnswerAssociationTypeEnumFE {
  POSITIVE = "positive",
  NEGATIVE = "negative",
}

// Corresponds to backend's QcaOut / QcaBase
export interface QCA {
  id: string;
  question_id: string;
  course_id: string;
  answer_association_type: AnswerAssociationTypeEnumFE;
  feedbacks_based_on_score?: ScoreFeedbackItemFE[] | null;
  // For UI convenience, you might want to populate question_title and course_name
  question_title?: string;
  course_name?: string;
}

// Corresponds to backend's QcaCreate
export interface QCACreate {
  question_id: string;
  course_id: string;
  answer_association_type: AnswerAssociationTypeEnumFE;
  feedbacks_based_on_score?: ScoreFeedbackItemFE[] | null;
}

// Corresponds to backend's QcaUpdate
export interface QCAUpdate {
  answer_association_type?: AnswerAssociationTypeEnumFE;
  feedbacks_based_on_score?: ScoreFeedbackItemFE[] | null;
}