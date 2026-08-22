/**
 * Auth Service — Sahayak AI
 * Calls backend auth endpoints via the shared Axios instance.
 * Returns typed responses — components never touch raw axios here.
 */

import apiClient from "@/lib/axios";
import type {
  RegisterRequest,
  LoginRequest,
  AuthTokenResponse,
  RefreshResponse,
  CurrentUserResponse,
  LogoutResponse,
} from "@/types/auth";

const BASE = "/api/v1/auth";

export const authService = {
  async register(data: RegisterRequest): Promise<AuthTokenResponse> {
    const res = await apiClient.post<AuthTokenResponse>(`${BASE}/register`, data);
    return res.data;
  },

  async login(data: LoginRequest): Promise<AuthTokenResponse> {
    const res = await apiClient.post<AuthTokenResponse>(`${BASE}/login`, data);
    return res.data;
  },

  async refresh(refreshToken: string): Promise<RefreshResponse> {
    const res = await apiClient.post<RefreshResponse>(`${BASE}/refresh`, {
      refresh_token: refreshToken,
    });
    return res.data;
  },

  async logout(): Promise<LogoutResponse> {
    const res = await apiClient.post<LogoutResponse>(`${BASE}/logout`);
    return res.data;
  },

  async me(): Promise<CurrentUserResponse> {
    const res = await apiClient.get<CurrentUserResponse>(`${BASE}/me`);
    return res.data;
  },
};
