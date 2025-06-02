import apiClient from './apiClient';
import type { QCA, QCACreate, QCAUpdate } from '../types/qcaTypes';

interface ListQCAsParams {
  question_id?: string;
  course_id?: string;
}

const qcaService = {
  listQCAs: async (params?: ListQCAsParams): Promise<QCA[]> => {
    const response = await apiClient.get<QCA[]>('/question-course-associations/', { params });
    return response.data;
  },

  getQCA: async (qcaId: string): Promise<QCA> => {
    const response = await apiClient.get<QCA>(`/question-course-associations/${qcaId}`);
    return response.data;
  },

  createQCA: async (data: QCACreate): Promise<QCA> => {
    const response = await apiClient.post<QCA>('/question-course-associations/', data);
    return response.data;
  },

  updateQCA: async (qcaId: string, data: QCAUpdate): Promise<QCA> => {
    const response = await apiClient.put<QCA>(`/question-course-associations/${qcaId}`, data);
    return response.data;
  },

  deleteQCA: async (qcaId: string): Promise<void> => {
    await apiClient.delete(`/question-course-associations/${qcaId}`);
  },
};

export default qcaService;