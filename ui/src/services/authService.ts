// ui/src/services/authService.ts
import apiClient from './apiClient';
import type{ User, UserLoginData, UserCreateData } from '../types/authTypes';

const signup = async (data: UserCreateData): Promise<User> => {
  const response = await apiClient.post<User>('/users/signup', data);
  return response.data;
};

const login = async (data: UserLoginData): Promise<User> => {
  const response = await apiClient.post<User>('/users/login', data);
  return response.data;
};

const logout = async (): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>('/users/logout');
  return response.data;
};

const getCurrentUser = async (): Promise<User | null> => {
  try {
    const response = await apiClient.get<User>('/users/me');
    return response.data;
  } catch (error: unknown) {
    // apiClient interceptor might handle 401 globally,
    // but specific handling here can be useful too.
    if (
      typeof error === 'object' &&
      error !== null &&
      'response' in error &&
      typeof (error as { response?: { status?: number } }).response === 'object' &&
      (error as { response?: { status?: number } }).response !== null &&
      (error as { response?: { status?: number } }).response?.status === 401
    ) {
      return null; // Explicitly return null for "not authenticated"
    }
    // For other errors, let them propagate to be handled by the caller
    throw error; 
  }
};

const authService = {
  signup,
  login,
  logout,
  getCurrentUser,
};

export default authService;