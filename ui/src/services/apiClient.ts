// ui/src/services/apiClient.ts
import axios from 'axios';

const API_PORT = 8000; // Standard port for your backend API
const API_PREFIX = '/api/v1';
let BASE_URL: string;

if (import.meta.env.MODE === 'development') {
  if (import.meta.env.VITE_API_DIRECT_URL) {
    // 1. Explicit override via .env.development.local (most reliable for manual dev)
    BASE_URL = `${import.meta.env.VITE_API_DIRECT_URL}${API_PREFIX}`;
    console.log("apiClient (Dev): Using explicit VITE_API_DIRECT_URL:", BASE_URL);
  } else if (typeof window !== 'undefined' && window.location.hostname && window.location.port === '5173') {
    // 2. Auto-detection for manual host development (Vite on 5173, API assumed on same host:8000)
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    BASE_URL = `${protocol}//${hostname}:${API_PORT}${API_PREFIX}`;
    console.log("apiClient (Dev): Auto-detecting API URL for direct Vite access:", BASE_URL);
  } else {
    // 3. Default for Docker dev (Nginx proxy from http://localhost/) or other scenarios
    BASE_URL = API_PREFIX; 
    console.log("apiClient (Dev): Using relative API prefix (likely via Nginx or similar):", BASE_URL);
  }
} else {
  // Production Mode
  BASE_URL = API_PREFIX;
  console.log("apiClient (Prod): Using relative API prefix:", BASE_URL);
}

const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Unauthorized access - API responded with 401.');
      // Consider more robust error handling or redirect
      // if (typeof window !== 'undefined' && !window.location.pathname.endsWith('/login')) {
      //   window.location.href = '/login';
      // }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
