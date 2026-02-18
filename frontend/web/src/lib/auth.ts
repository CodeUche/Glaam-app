"use client";

import { create } from "zustand";
import api, { setTokens, clearTokens, getAccessToken } from "./api";
import type {
  User,
  AuthTokens,
  LoginCredentials,
  RegisterData,
} from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  initialize: async () => {
    const token = getAccessToken();
    if (token) {
      try {
        await get().fetchUser();
      } catch {
        clearTokens();
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },

  login: async (credentials: LoginCredentials) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.post<AuthTokens & { user: User }>(
        "/auth/login/",
        credentials
      );
      setTokens(data.access, data.refresh);
      set({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Login failed. Please check your credentials.";
      set({ isLoading: false, error: message });
      throw new Error(message);
    }
  },

  register: async (data: RegisterData) => {
    set({ isLoading: true, error: null });
    try {
      const { data: responseData } = await api.post<
        AuthTokens & { user: User }
      >("/auth/register/", data);
      setTokens(responseData.access, responseData.refresh);
      set({
        user: responseData.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      const errorData = (
        err as { response?: { data?: Record<string, string[]> } }
      )?.response?.data;
      const message =
        errorData && typeof errorData === "object"
          ? Object.values(errorData).flat().join(" ")
          : "Registration failed. Please try again.";
      set({ isLoading: false, error: message });
      throw new Error(message);
    }
  },

  logout: () => {
    clearTokens();
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  },

  fetchUser: async () => {
    try {
      const { data } = await api.get<User>("/auth/me/");
      set({ user: data, isAuthenticated: true, isLoading: false });
    } catch {
      clearTokens();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
