import { create } from 'zustand';
import apiClient from '@/api/client';

interface User {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  tenant_id: string | null;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  user: null,

  fetchUser: async () => {
    try {
      const response = await apiClient.get('/auth/me');
      set({ user: response.data });
    } catch (error) {
      console.error("Failed to fetch user:", error);
      get().logout(); // Logout if user fetch fails
    }
  },

  login: async (email, password) => {
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { access_token, refresh_token } = response.data;

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      set({ accessToken: access_token, refreshToken: refresh_token, isAuthenticated: true });
      await get().fetchUser(); // Fetch user info after login
      return true;
    } catch (error) {
      console.error("Login failed:", error);
      return false;
    }
  },

  logout: () => {
    localStorage.clear();
    delete apiClient.defaults.headers.common['Authorization'];
    set({ accessToken: null, refreshToken: null, isAuthenticated: false, user: null });
  },
}));

// Fetch user on initial load if authenticated
if (useAuthStore.getState().isAuthenticated) {
  useAuthStore.getState().fetchUser();
}
