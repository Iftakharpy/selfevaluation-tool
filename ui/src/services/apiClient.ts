// ui/src/services/apiClient.ts
import axios from 'axios';

const API_INTERNAL_PORT = '8000'; // Internal port of the API container
const API_PREFIX = '/api/v1';
let BASE_URL: string;

const IS_DEVELOPMENT = import.meta.env.MODE === 'development';
const VITE_API_DIRECT_URL_FROM_ENV = import.meta.env.VITE_API_DIRECT_URL as string | undefined;

if (IS_DEVELOPMENT) {
  if (VITE_API_DIRECT_URL_FROM_ENV) {
    // 1. Explicit override via .env file (e.g., VITE_API_DIRECT_URL=http://localhost:8001)
    // This URL should already include the host and port for the API, not the prefix.
    BASE_URL = `${VITE_API_DIRECT_URL_FROM_ENV}${API_PREFIX}`;
    console.log("apiClient (Dev): Using explicit VITE_API_DIRECT_URL:", BASE_URL);
  } else if (typeof window !== 'undefined' && window.location.port === '5174') {
    // 2. Accessing Vite dev server directly on its mapped host port (e.g., http://localhost:5174)
    // In this scenario, the API calls should target the Nginx dev proxy or the API's mapped host port.
    const { protocol, hostname } = window.location;
    // Option: Target the Nginx dev proxy (typically on 8080)
    // BASE_URL = `${protocol}//${hostname}:8080${API_PREFIX}`;
    // console.log("apiClient (Dev): Vite direct access (5174), assuming API via Nginx dev proxy on 8080:", BASE_URL);
    // Option: Target the API container's directly mapped host port (e.g., 8001)
    BASE_URL = `${protocol}//${hostname}:8001${API_PREFIX}`; 
    console.log("apiClient (Dev): Vite direct access (5174), pointing API to mapped host port 8001:", BASE_URL);
  } else {
    // 3. Default for Docker dev when accessing through Nginx dev proxy (e.g., http://localhost:8080)
    // The Nginx proxy handles routing /api/v1 to the API container.
    BASE_URL = API_PREFIX; // Relative path, e.g., /api/v1
    console.log("apiClient (Dev): Using relative API prefix (likely via Nginx dev proxy):", BASE_URL);
  }
} else {
  // Production Mode: UI is served by Nginx, API calls are relative to the domain.
  BASE_URL = API_PREFIX; // e.g., /api/v1
  console.log("apiClient (Prod): Using relative API prefix:", BASE_URL);
}

console.log(`apiClient: Final API BASE_URL determined as: ${BASE_URL}`);

const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      console.error('Unauthorized access - API responded with 401. Redirecting to login.');
      // Avoid redirect loops if already on login page
      if (!window.location.pathname.endsWith('/login')) {
        // window.location.href = '/login'; // Consider a more React-router friendly redirect
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;