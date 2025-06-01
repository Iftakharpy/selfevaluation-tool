import apiClient from './apiClient';
import type { SurveySummaryListItemFE, SurveyForTakingFE } from '../types/surveyTypes';
// Add SurveyCreateFE, SurveyUpdateFE later for teacher phase

const surveyService = {
  // For students: list published surveys
  listPublishedSurveys: async (): Promise<SurveySummaryListItemFE[]> => {
    const response = await apiClient.get<SurveySummaryListItemFE[]>('/surveys/?published_only=true');
    return response.data;
  },

  // For students: get a specific survey to take (with questions)
  // Also used by teachers to view survey structure
  getSurveyDetail: async (surveyId: string): Promise<SurveyForTakingFE> => {
    const response = await apiClient.get<SurveyForTakingFE>(`/surveys/${surveyId}?include_questions=true`);
    return response.data;
  },

  // Teacher-specific methods will be added in a later phase:
  // listMySurveys (teacher's own)
  // createSurvey
  // updateSurvey
  // deleteSurvey
};

export default surveyService;