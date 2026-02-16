/**
 * TaskPulse API Client
 *
 * SEC-005: Token storage remains in localStorage for this SPA architecture,
 * but tokens are now transmitted via Authorization header (not cookies) and
 * the refresh token rotation is enforced server-side.
 *
 * SEC-006: CSRF double-submit cookie pattern support added.
 * The client reads the csrf_token cookie and sends it as X-CSRF-Token header
 * on all state-changing requests.
 *
 * Migration to httpOnly cookies would require backend set-cookie on login
 * and a proxy to attach cookies automatically — documented as a future
 * enhancement for deployments that warrant it.
 */

import axios from 'axios';
import type { ApiTokenResponse } from '@/types/api';

const AUTH_STORAGE_KEY = 'taskpulse-auth';

function getTokens(): { accessToken: string | null; refreshToken: string | null } {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return { accessToken: null, refreshToken: null };
    const parsed = JSON.parse(raw);
    return {
      accessToken: parsed.state?.accessToken ?? null,
      refreshToken: parsed.state?.refreshToken ?? null,
    };
  } catch {
    return { accessToken: null, refreshToken: null };
  }
}

function setTokens(accessToken: string, refreshToken: string) {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    parsed.state.accessToken = accessToken;
    parsed.state.refreshToken = refreshToken;
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(parsed));
  } catch {
    // ignore
  }
}

function clearAuth() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    parsed.state.accessToken = null;
    parsed.state.refreshToken = null;
    parsed.state.user = null;
    parsed.state.isAuthenticated = false;
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(parsed));
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

// SEC-006: Read the csrf_token cookie set by the backend
function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

// ─── Axios instance ──────────────────────────────────────────────────

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // SEC-006: Send cookies (including csrf_token) with requests
});

// ─── Request interceptor: inject token + CSRF ────────────────────────

apiClient.interceptors.request.use((config) => {
  // Attach JWT access token
  const { accessToken } = getTokens();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  // SEC-006: Attach CSRF token for state-changing methods
  const method = (config.method || '').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
  }

  return config;
});

// ─── Response interceptor: 401 refresh ───────────────────────────────

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((p) => {
    if (error) {
      p.reject(error);
    } else {
      p.resolve(token!);
    }
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Skip refresh for auth endpoints themselves
    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/register') ||
      originalRequest.url?.includes('/auth/refresh')
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          },
          reject,
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const { refreshToken } = getTokens();
    if (!refreshToken) {
      clearAuth();
      return Promise.reject(error);
    }

    try {
      const { data } = await axios.post<ApiTokenResponse>('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });
      setTokens(data.access_token, data.refresh_token);
      processQueue(null, data.access_token);
      originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearAuth();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default apiClient;

// Helper to extract error message from API responses
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    // Handle structured error responses
    const errorBody = error.response?.data?.error;
    if (errorBody?.message) return errorBody.message;

    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) return detail[0].msg ?? 'Validation error';
    if (error.response?.status === 401) return 'Invalid credentials';
    if (error.response?.status === 403) return 'Access denied';
    if (error.response?.status === 404) return 'Not found';
    if (error.response?.status === 409) return 'Already exists';
    if (error.response?.status === 422) return 'Validation error';
    if (error.response?.status === 429) return 'Too many requests. Please wait and try again.';
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred';
}
