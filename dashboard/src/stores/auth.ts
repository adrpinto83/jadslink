import { create } from 'zustand';
import apiClient from '@/api/client';

interface User {
  id: string;
  email: string;
  role: string;  // Rol global: superadmin, operator
  tenant_role?: string;  // Rol dentro del tenant: owner, admin, collaborator, viewer
  is_active: boolean;
  tenant_id: string | null;
}

interface AuthState {
  accessToken: string | null;
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  setAccessToken: (token: string | null) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,  // Only in memory (lost on page reload)
  isAuthenticated: false,
  user: null,
  loading: true,

  fetchUser: async () => {
    set({ loading: true });
    try {
      const response = await apiClient.get('/auth/me');
      set({ user: response.data, loading: false });
    } catch (error) {
      console.error("Failed to fetch user:", error);
      set({ loading: false });
      get().logout();
    }
  },

  login: async (email, password) => {
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { access_token } = response.data;

      // Store access token in memory only (not localStorage)
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      set({ accessToken: access_token, isAuthenticated: true });
      await get().fetchUser();
      return true;
    } catch (error) {
      console.error("Login failed:", error);
      return false;
    }
  },

  logout: () => {
    delete apiClient.defaults.headers.common['Authorization'];
    set({ accessToken: null, isAuthenticated: false, user: null });
  },

  setAccessToken: (token: string | null) => {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
    }
    set({ accessToken: token, isAuthenticated: !!token });
  },
}));

// Try to fetch user on initial load if there's an access token in memory
// Note: Access token is lost on page reload, user will need to login again
// This is intended behavior for security (prevent token theft via XSS)
