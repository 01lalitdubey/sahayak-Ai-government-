/**
 * Global TypeScript Types — Sahayak AI
 * Shared types used across components, stores, and services.
 * Domain-specific types live in their own files (e.g. types/scheme.ts).
 */

// ── API Response Envelopes ────────────────────────────────────────────────
export interface ApiSuccessResponse<T = unknown> {
  success: true;
  message: string;
  data: T | null;
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  status_code: number;
  errors: Array<{ field?: string; message: string }>;
}

export type ApiResponse<T = unknown> = ApiSuccessResponse<T> | ApiErrorResponse;

export interface PaginatedResponse<T> {
  success: true;
  data: T[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

// ── Navigation ────────────────────────────────────────────────────────────
export interface NavItem {
  label: string;
  href: string;
  icon?: string;
  badge?: string;
  children?: NavItem[];
}

// ── Theme ─────────────────────────────────────────────────────────────────
export type Theme = "light" | "dark" | "system";

// ── Common UI ─────────────────────────────────────────────────────────────
export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}
