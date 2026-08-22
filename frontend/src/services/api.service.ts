/**
 * Base API Service — Sahayak AI
 * Thin wrapper around the Axios instance.
 * All domain services extend or compose this.
 *
 * NOTE: The axios interceptor throws on API errors, so these methods
 * always resolve with the success response shape. The return type
 * is ApiSuccessResponse<T> (not the full union) so callers can safely
 * access .data without type narrowing.
 */

import apiClient from "@/lib/axios";
import type { ApiSuccessResponse } from "@/types";

export const apiService = {
  async get<T>(url: string, params?: Record<string, unknown>): Promise<ApiSuccessResponse<T>> {
    const res = await apiClient.get<ApiSuccessResponse<T>>(url, { params });
    return res.data;
  },

  async post<T>(url: string, body?: unknown): Promise<ApiSuccessResponse<T>> {
    const res = await apiClient.post<ApiSuccessResponse<T>>(url, body);
    return res.data;
  },

  async put<T>(url: string, body?: unknown): Promise<ApiSuccessResponse<T>> {
    const res = await apiClient.put<ApiSuccessResponse<T>>(url, body);
    return res.data;
  },

  async patch<T>(url: string, body?: unknown): Promise<ApiSuccessResponse<T>> {
    const res = await apiClient.patch<ApiSuccessResponse<T>>(url, body);
    return res.data;
  },

  async delete<T>(url: string): Promise<ApiSuccessResponse<T>> {
    const res = await apiClient.delete<ApiSuccessResponse<T>>(url);
    return res.data;
  },
};
