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
  initializeFromStorage: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
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

  initializeFromStorage: async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (token) {
        console.log('[Auth] Token found in localStorage, restoring...');
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        set({ accessToken: token, isAuthenticated: true });

        // Verify token is still valid
        try {
          const response = await apiClient.get('/auth/me');
          set({ user: response.data, loading: false });
        } catch (err) {
          console.error('[Auth] Token validation failed, clearing storage');
          get().logout();
        }
      } else {
        set({ loading: false });
      }
    } catch (error) {
      console.error('[Auth] Failed to initialize from storage:', error);
      set({ loading: false });
    }
  },

  login: async (email, password) => {
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { access_token } = response.data;

      // Store access token in localStorage AND memory
      localStorage.setItem('accessToken', access_token);
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
    localStorage.removeItem('accessToken');
    delete apiClient.defaults.headers.common['Authorization'];
    set({ accessToken: null, isAuthenticated: false, user: null });
  },

  setAccessToken: (token: string | null) => {
    if (token) {
      localStorage.setItem('accessToken', token);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      localStorage.removeItem('accessToken');
      delete apiClient.defaults.headers.common['Authorization'];
    }
    set({ accessToken: token, isAuthenticated: !!token });
  },
}));

// Initialize from localStorage on app startup
useAuthStore.getState().initializeFromStorage();
