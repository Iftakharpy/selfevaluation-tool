import apiClient from './apiClient';
import type { Course, CourseCreate, CourseUpdate } from '../types/courseTypes';

const courseService = {
  listCourses: async (): Promise<Course[]> => {
    const response = await apiClient.get<Course[]>('/courses/');
    return response.data;
  },

  getCourse: async (courseId: string): Promise<Course> => {
    const response = await apiClient.get<Course>(`/courses/${courseId}`);
    return response.data;
  },

  createCourse: async (data: CourseCreate): Promise<Course> => {
    const response = await apiClient.post<Course>('/courses/', data);
    return response.data;
  },

  updateCourse: async (courseId: string, data: CourseUpdate): Promise<Course> => {
    const response = await apiClient.put<Course>(`/courses/${courseId}`, data);
    return response.data;
  },

  deleteCourse: async (courseId: string): Promise<void> => {
    await apiClient.delete(`/courses/${courseId}`);
  },
};

export default courseService;