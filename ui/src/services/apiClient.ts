import axios from 'axios';

const IS_DEV = import.meta.env.DEV;
const API_PREFIX = '/api/v1';

const BASE_URL = IS_DEV 
  ? `${window.location.protocol}//${window.location.hostname}:8000${API_PREFIX}` 
  : API_PREFIX;

const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // Important for session cookies
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access, e.g., redirect to login
      // Consider dispatching a custom event or calling a logout function from AuthContext
      console.error('Unauthorized access - API responded with 401.');
      // Example: window.location.href = '/login'; // This is a hard redirect
    }
    return Promise.reject(error);
  }
);

export default apiClient;
