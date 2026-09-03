/**
 * Axios Instance — Sahayak AI
 * Production-ready HTTP client with:
 *  - Automatic Bearer token injection
 *  - 401 → refresh → retry flow
 *  - Logout on refresh failure
 */

import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import { API_BASE_URL } from "@/lib/constants";
import { tokenStorage } from "@/lib/token-storage";

// Flag to prevent multiple concurrent refresh calls
let _isRefreshing = false;
// Queue of failed requests waiting for the refresh to complete
let _failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null) {
  _failedQueue.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token!);
  });
  _failedQueue = [];
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ── Request Interceptor ────────────────────────────────────────────────────
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Extract locale from URL path (next-intl uses URL-based routing)
    // URL pattern: /hi/schemes, /ta/schemes, /en/schemes, or /schemes (default en)
    if (typeof window !== "undefined") {
      const pathLocale = window.location.pathname.split("/")[1];
      // Check if the first path segment is a known locale
      const knownLocales = ["hi", "ta", "te", "mr", "gu", "bn", "kn", "ml", "pa", "or", "as", "ur"];
      if (pathLocale && knownLocales.includes(pathLocale)) {
        config.headers["Accept-Language"] = pathLocale;
      } else {
        // Fallback: check NEXT_LOCALE cookie
        const match = document.cookie.match(new RegExp("(^| )NEXT_LOCALE=([^;]+)"));
        if (match) {
          config.headers["Accept-Language"] = match[2];
        }
        // If no locale found → backend defaults to 'en' which is correct
      }
    }

    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

// ── Response Interceptor ───────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Only intercept 401 on non-auth endpoints to avoid infinite loops
    const isAuthEndpoint =
      originalRequest.url?.includes("/auth/login") ||
      originalRequest.url?.includes("/auth/register") ||
      originalRequest.url?.includes("/auth/refresh");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (_isRefreshing) {
        // Queue this request until the ongoing refresh finishes
        return new Promise((resolve, reject) => {
          _failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      _isRefreshing = true;

      const refreshToken = tokenStorage.getRefreshToken();

      if (!refreshToken) {
        _isRefreshing = false;
        _clearAndRedirect();
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken },
          { headers: { "Content-Type": "application/json" } },
        );

        const { access_token, refresh_token: new_refresh } = response.data;
        tokenStorage.setAccessToken(access_token);
        tokenStorage.setRefreshToken(new_refresh);

        // Update Zustand store without importing it (avoids circular deps)
        // The store reads from tokenStorage on next render cycle
        processQueue(null, access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        _clearAndRedirect();
        return Promise.reject(refreshError);
      } finally {
        _isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

function _clearAndRedirect() {
  tokenStorage.clearAll();
  if (typeof window !== "undefined") {
    window.location.href = "/login?session=expired";
  }
}

export default apiClient;
