/**
 * Auth Types — Sahayak AI
 * Matches the backend Pydantic schemas exactly.
 */

export type UserRole = "user" | "admin" | "super_admin";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

// ── API request shapes ────────────────────────────────────────────────────

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
  confirm_password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

// ── API response shapes ───────────────────────────────────────────────────

export interface AuthTokenResponse {
  success: boolean;
  message: string;
  data: AuthUser;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshResponse {
  success: boolean;
  message: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CurrentUserResponse {
  success: boolean;
  message: string;
  data: AuthUser;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}

// ── Storage keys ──────────────────────────────────────────────────────────

export const TOKEN_KEYS = {
  ACCESS: "sahayak_access_token",
  REFRESH: "sahayak_refresh_token",
  USER: "sahayak_user",
} as const;
