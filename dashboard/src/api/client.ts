import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Store CSRF token in memory
let csrfToken: string | null = null;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Send cookies with every request
});

// Request interceptor to add CSRF token and authorization
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token to headers for state-changing requests
    if (['POST', 'PATCH', 'DELETE', 'PUT'].includes(config.method?.toUpperCase() || '')) {
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiration/refresh and extract CSRF token
apiClient.interceptors.response.use(
  (response) => {
    // Extract CSRF token from response header (sent on every response)
    const newCsrfToken = response.headers['x-csrf-token'];
    if (newCsrfToken) {
      csrfToken = newCsrfToken;
    }

    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Extract CSRF token from error response if available
    if (error.response?.headers['x-csrf-token']) {
      csrfToken = error.response.headers['x-csrf-token'];
    }

    // If error is 401 and not a refresh token request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // Call refresh endpoint (refresh_token comes from HttpOnly cookie automatically)
        const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, {
          withCredentials: true,
        });

        const { access_token } = refreshResponse.data;

        // Update access token in memory via auth store
        useAuthStore.getState().setAccessToken(access_token);

        // Extract CSRF token from refresh response
        if (refreshResponse.headers['x-csrf-token']) {
          csrfToken = refreshResponse.headers['x-csrf-token'];
        }

        // Retry original request with new token and CSRF token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        if (csrfToken && ['POST', 'PATCH', 'DELETE', 'PUT'].includes(originalRequest.method.toUpperCase())) {
          originalRequest.headers['X-CSRF-Token'] = csrfToken;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh token failed (or expired), redirect to login
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // If error is 403 (CSRF validation failed), redirect to login
    if (error.response?.status === 403) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

// Fetch initial CSRF token
apiClient.get('/auth/me').catch(() => {
  // It's ok if this fails, we'll get CSRF token from next request
});

export default apiClient;
