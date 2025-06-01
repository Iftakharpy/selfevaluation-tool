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

  // Use this if you want to save answers periodically or one by one
  // The backend endpoint expects a list, so we wrap a single answer in a list.
  saveAnswer: async (attemptId: string, answer: StudentAnswerPayloadFE): Promise<StudentAnswerFE> => {
    const response = await apiClient.post<StudentAnswerFE[]>(`/survey-attempts/${attemptId}/answers`, { answers: [answer] });
    if (response.data && response.data.length > 0) {
        return response.data[0]; // Assuming API returns the saved answer(s)
    }
    throw new Error("Failed to save answer or no answer data returned.");
  },

  // Use this for submitting a batch of answers, perhaps before final submit
  submitAnswers: async (attemptId: string, answers: StudentAnswerPayloadFE[]): Promise<StudentAnswerFE[]> => {
    const response = await apiClient.post<StudentAnswerFE[]>(`/survey-attempts/${attemptId}/answers`, { answers });
    return response.data;
  },

  // Final submission of the survey attempt
  submitSurvey: async (attemptId: string): Promise<SurveyAttemptResultFE> => {
    const response = await apiClient.post<SurveyAttemptResultFE>(`/survey-attempts/${attemptId}/submit`);
    return response.data;
  },

  // For students to list their own attempts
  getMyAttempts: async (): Promise<SurveyAttemptListItemFE[]> => {
    // Consider adding survey titles to the backend response for this endpoint
    // or making an additional fetch if needed. For now, assume backend sends enough.
    const response = await apiClient.get<SurveyAttemptListItemFE[]>('/survey-attempts/my');
    return response.data;
  },

  // For students or teachers to get results of a specific submitted attempt
  getAttemptResult: async (attemptId: string): Promise<SurveyAttemptResultFE> => {
    const response = await apiClient.get<SurveyAttemptResultFE>(`/survey-attempts/${attemptId}/results`);
    return response.data;
  },

  // Teacher-specific: list all attempts for a survey they own
  // listAttemptsForSurvey: async (surveyId: string): Promise<SurveyAttemptListItemFE[]> => {
  //   const response = await apiClient.get<SurveyAttemptListItemFE[]>(`/survey-attempts/by-survey/${surveyId}`);
  //   return response.data;
  // }
};

export default surveyAttemptService;