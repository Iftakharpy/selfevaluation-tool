// File: ui/src/services/surveyService.ts
import apiClient from './apiClient';
import type { 
    SurveySummaryListItemFE, 
    SurveyFE, // Use the more general SurveyFE
    SurveyCreateFE, 
    SurveyUpdateFE 
} from '../types/surveyTypes';

const surveyService = {
  // For students: list published surveys
  listPublishedSurveys: async (): Promise<SurveySummaryListItemFE[]> => {
    const response = await apiClient.get<SurveySummaryListItemFE[]>('/surveys/?published_only=true');
    return response.data;
  },

  // For students: get a specific survey to take (with questions)
  // Also used by teachers to view survey structure or get data for editing
  getSurveyDetail: async (surveyId: string): Promise<SurveyFE> => {
    const response = await apiClient.get<SurveyFE>(`/surveys/${surveyId}?include_questions=true`);
    return response.data;
  },

  // --- NEW METHODS FOR TEACHER SURVEY MANAGEMENT ---

  // For teachers to list all surveys (or filter by their own, depending on backend)
  // The current backend returns all surveys for a teacher if published_only is not specified.
  // Client-side filtering might be needed in the page component if "my surveys only" is desired.
  listAllSurveysForTeacher: async (params?: { published_only?: boolean }): Promise<SurveySummaryListItemFE[]> => {
    const response = await apiClient.get<SurveySummaryListItemFE[]>('/surveys/', { params });
    return response.data;
  },
  
  createSurvey: async (data: SurveyCreateFE): Promise<SurveyFE> => {
    const response = await apiClient.post<SurveyFE>('/surveys/', data);
    return response.data;
  },

  updateSurvey: async (surveyId: string, data: SurveyUpdateFE): Promise<SurveyFE> => {
    const response = await apiClient.put<SurveyFE>(`/surveys/${surveyId}`, data);
    return response.data;
  },

  deleteSurvey: async (surveyId: string): Promise<void> => {
    await apiClient.delete(`/surveys/${surveyId}`);
  },
};

export default surveyService;