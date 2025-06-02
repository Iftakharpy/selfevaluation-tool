import apiClient from './apiClient';
import type { QuestionListItemFE, QuestionFE, QuestionCreateFE, QuestionUpdateFE } from '../types/questionTypes';

const questionService = {
  listQuestions: async (): Promise<QuestionListItemFE[]> => {
    const response = await apiClient.get<QuestionListItemFE[]>('/questions/');
    return response.data;
  },

  getQuestion: async (questionId: string): Promise<QuestionFE> => {
    const response = await apiClient.get<QuestionFE>(`/questions/${questionId}`);
    return response.data;
  },

  createQuestion: async (data: QuestionCreateFE): Promise<QuestionFE> => {
    const response = await apiClient.post<QuestionFE>('/questions/', data);
    return response.data;
  },

  updateQuestion: async (questionId: string, data: QuestionUpdateFE): Promise<QuestionFE> => {
    const response = await apiClient.put<QuestionFE>(`/questions/${questionId}`, data);
    return response.data;
  },

  deleteQuestion: async (questionId: string): Promise<void> => {
    await apiClient.delete(`/questions/${questionId}`);
  },
};

export default questionService;