import { create } from 'zustand';
import api, { storeTokens, clearTokens, getStoredTokens } from './api';
import {
  User,
  AuthTokens,
  LoginCredentials,
  RegisterData,
} from '../types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;

  initialize: () => Promise<void>;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  isInitialized: false,
  error: null,

  initialize: async () => {
    try {
      set({ isLoading: true });
      const tokens = await getStoredTokens();
      if (tokens?.access) {
        await get().fetchUser();
      }
    } catch {
      await clearTokens();
      set({ user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false, isInitialized: true });
    }
  },

  login: async (credentials: LoginCredentials) => {
    try {
      set({ isLoading: true, error: null });

      const { data } = await api.post<AuthTokens & { user: User }>(
        '/auth/login/',
        credentials,
      );

      await storeTokens({ access: data.access, refresh: data.refresh });

      set({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        'Login failed. Please check your credentials.';
      set({ isLoading: false, error: message });
      throw new Error(message);
    }
  },

  register: async (data: RegisterData) => {
    try {
      set({ isLoading: true, error: null });

      const { data: responseData } = await api.post<
        AuthTokens & { user: User }
      >('/auth/register/', data);

      await storeTokens({
        access: responseData.access,
        refresh: responseData.refresh,
      });

      set({
        user: responseData.user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.email?.[0] ||
        'Registration failed. Please try again.';
      set({ isLoading: false, error: message });
      throw new Error(message);
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout/');
    } catch {
      // Ignore errors on logout call
    } finally {
      await clearTokens();
      set({
        user: null,
        isAuthenticated: false,
        error: null,
      });
    }
  },

  fetchUser: async () => {
    try {
      const { data } = await api.get<User>('/auth/me/');
      set({ user: data, isAuthenticated: true });
    } catch {
      await clearTokens();
      set({ user: null, isAuthenticated: false });
    }
  },

  updateProfile: async (profileData: Partial<User>) => {
    try {
      set({ isLoading: true, error: null });
      const { data } = await api.patch<User>('/auth/me/', profileData);
      set({ user: data, isLoading: false });
    } catch (err: any) {
      const message =
        err.response?.data?.detail || 'Failed to update profile.';
      set({ isLoading: false, error: message });
      throw new Error(message);
    }
  },

  clearError: () => set({ error: null }),
}));
