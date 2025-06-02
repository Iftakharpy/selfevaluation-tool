// File: ui/src/services/surveyAttemptService.ts
import apiClient from './apiClient';
import type {
  SurveyAttemptStartFE,
  StudentAnswerPayloadFE,
  StudentAnswerFE,
  SurveyAttemptResultFE,
  SurveyAttemptListItemFE,
} from '../types/surveyAttemptTypes';

const surveyAttemptService = {
  startSurveyAttempt: async (surveyId: string): Promise<SurveyAttemptStartFE> => {
    const response = await apiClient.post<SurveyAttemptStartFE>('/survey-attempts/start', { survey_id: surveyId });
    return response.data;
  },

  saveAnswer: async (attemptId: string, answer: StudentAnswerPayloadFE): Promise<StudentAnswerFE> => {
    const response = await apiClient.post<StudentAnswerFE[]>(`/survey-attempts/${attemptId}/answers`, { answers: [answer] });
    if (response.data && response.data.length > 0) {
        return response.data[0];
    }
    throw new Error("Failed to save answer or no answer data returned.");
  },

  submitAnswers: async (attemptId: string, answers: StudentAnswerPayloadFE[]): Promise<StudentAnswerFE[]> => {
    const response = await apiClient.post<StudentAnswerFE[]>(`/survey-attempts/${attemptId}/answers`, { answers });
    return response.data;
  },

  submitSurvey: async (attemptId: string): Promise<SurveyAttemptResultFE> => {
    const response = await apiClient.post<SurveyAttemptResultFE>(`/survey-attempts/${attemptId}/submit`);
    return response.data;
  },

  getMyAttempts: async (): Promise<SurveyAttemptListItemFE[]> => {
    const response = await apiClient.get<SurveyAttemptListItemFE[]>('/survey-attempts/my');
    return response.data;
  },

  getAttemptResult: async (attemptId: string): Promise<SurveyAttemptResultFE> => {
    const response = await apiClient.get<SurveyAttemptResultFE>(`/survey-attempts/${attemptId}/results`);
    return response.data;
  },

  // --- METHOD FOR TEACHER ---
  listAttemptsForSurvey: async (surveyId: string, includeAnswers = false): Promise<SurveyAttemptListItemFE[]> => {
    const response = await apiClient.get<SurveyAttemptListItemFE[]>(`/survey-attempts/by-survey/${surveyId}`, {
        params: { include_answers: includeAnswers } 
    });
    return response.data;
  }
};

export default surveyAttemptService;