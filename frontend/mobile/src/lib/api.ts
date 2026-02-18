import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthTokens } from '../types';

const API_URL = process.env.API_URL || 'http://localhost:8000/api/v1';

const STORAGE_KEYS = {
  ACCESS_TOKEN: '@glamconnect_access_token',
  REFRESH_TOKEN: '@glamconnect_refresh_token',
};

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ---------- Token helpers ----------

export async function getStoredTokens(): Promise<AuthTokens | null> {
  try {
    const access = await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    const refresh = await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    if (access && refresh) {
      return { access, refresh };
    }
    return null;
  } catch {
    return null;
  }
}

export async function storeTokens(tokens: AuthTokens): Promise<void> {
  await AsyncStorage.multiSet([
    [STORAGE_KEYS.ACCESS_TOKEN, tokens.access],
    [STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh],
  ]);
}

export async function clearTokens(): Promise<void> {
  await AsyncStorage.multiRemove([
    STORAGE_KEYS.ACCESS_TOKEN,
    STORAGE_KEYS.REFRESH_TOKEN,
  ]);
}

// ---------- Request interceptor: attach access token ----------

api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const tokens = await getStoredTokens();
    if (tokens?.access) {
      config.headers.Authorization = `Bearer ${tokens.access}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ---------- Response interceptor: auto-refresh on 401 ----------

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Only attempt refresh on 401, if not already retried, and not a refresh request
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh/')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(api(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const tokens = await getStoredTokens();
        if (!tokens?.refresh) {
          throw new Error('No refresh token available');
        }

        const { data } = await axios.post<{ access: string }>(
          `${API_URL}/auth/refresh/`,
          { refresh: tokens.refresh },
        );

        await storeTokens({ access: data.access, refresh: tokens.refresh });

        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        processQueue(null, data.access);

        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        await clearTokens();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export default api;
