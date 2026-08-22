/**
 * Scheme Service — Sahayak AI
 * All HTTP calls to /api/v1/schemes/* and /api/v1/admin/schemes/* go through here.
 */

import apiClient from "@/lib/axios";
import type {
  SchemeListResponse,
  SchemeResponse,
  CategoriesResponse,
  StatesResponse,
  SchemeFilters,
  AdminSchemeFilters,
  SchemeCreatePayload,
  SchemeUpdatePayload,
  TranslationStatusResponse,
  AuditHistoryResponse,
} from "@/types/scheme";

const BASE = "/api/v1/schemes";
const ADMIN_BASE = "/api/v1/admin/schemes";

function buildParams(filters: Partial<SchemeFilters>): Record<string, string> {
  const p: Record<string, string> = {};
  if (filters.query) p["query"] = filters.query;
  if (filters.category) p["category"] = filters.category;
  if (filters.scheme_type) p["scheme_type"] = filters.scheme_type;
  if (filters.application_mode) p["application_mode"] = filters.application_mode;
  if (filters.state) p["state"] = filters.state;
  if (filters.ministry) p["ministry"] = filters.ministry;
  if (filters.is_featured != null) p["is_featured"] = String(filters.is_featured);
  if (filters.is_active != null) p["is_active"] = String(filters.is_active);
  if (filters.sort) p["sort"] = filters.sort;
  if (filters.page) p["page"] = String(filters.page);
  if (filters.page_size) p["page_size"] = String(filters.page_size);
  return p;
}

function buildAdminParams(filters: Partial<AdminSchemeFilters>): Record<string, string> {
  const p = buildParams(filters);
  // For admin, is_active=undefined means show all (no filter) — don't add the key
  if (filters.is_active === undefined || filters.is_active === null) {
    delete p["is_active"];
  }
  return p;
}

export const schemeService = {
  // ── Public API ──────────────────────────────────────────────────────────

  async getSchemes(filters: Partial<SchemeFilters> = {}): Promise<SchemeListResponse> {
    const res = await apiClient.get<SchemeListResponse>(BASE, { params: buildParams(filters) });
    return res.data;
  },

  async getScheme(id: string): Promise<SchemeResponse> {
    const res = await apiClient.get<SchemeResponse>(`${BASE}/${id}`);
    return res.data;
  },

  async getSchemeByCode(code: string): Promise<SchemeResponse> {
    const res = await apiClient.get<SchemeResponse>(`${BASE}/code/${code}`);
    return res.data;
  },

  async getFeatured(limit = 6): Promise<SchemeListResponse> {
    const res = await apiClient.get<SchemeListResponse>(`${BASE}/featured`, { params: { limit } });
    return res.data;
  },

  async getRecent(limit = 6): Promise<SchemeListResponse> {
    const res = await apiClient.get<SchemeListResponse>(`${BASE}/recent`, { params: { limit } });
    return res.data;
  },

  async getCategories(): Promise<CategoriesResponse> {
    const res = await apiClient.get<CategoriesResponse>(`${BASE}/categories`);
    return res.data;
  },

  async getStates(): Promise<StatesResponse> {
    const res = await apiClient.get<StatesResponse>(`${BASE}/states`);
    return res.data;
  },

  // ── Admin CRUD ──────────────────────────────────────────────────────────

  async createScheme(payload: SchemeCreatePayload): Promise<SchemeResponse> {
    // Remove empty strings for optional fields
    const clean = Object.fromEntries(
      Object.entries(payload).filter(([, v]) => v !== "" && v !== null && v !== undefined)
    );
    const res = await apiClient.post<SchemeResponse>(BASE, clean);
    return res.data;
  },

  async updateScheme(id: string, payload: SchemeUpdatePayload): Promise<SchemeResponse> {
    const clean = Object.fromEntries(
      Object.entries(payload).filter(([, v]) => v !== "" && v !== null && v !== undefined)
    );
    const res = await apiClient.put<SchemeResponse>(`${BASE}/${id}`, clean);
    return res.data;
  },

  async updateStatus(id: string, is_active: boolean): Promise<SchemeResponse> {
    const res = await apiClient.patch<SchemeResponse>(`${BASE}/${id}/status`, { is_active });
    return res.data;
  },

  async deleteScheme(id: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.delete(`${BASE}/${id}`);
    return res.data;
  },

  async restoreScheme(id: string): Promise<SchemeResponse> {
    const res = await apiClient.patch<SchemeResponse>(`${BASE}/${id}/restore`);
    return res.data;
  },

  // ── Admin Lifecycle Management ──────────────────────────────────────────

  async getAdminSchemes(filters: Partial<AdminSchemeFilters> = {}): Promise<SchemeListResponse> {
    const res = await apiClient.get<SchemeListResponse>(ADMIN_BASE, { params: buildAdminParams(filters) });
    return res.data;
  },

  async getAdminScheme(id: string): Promise<SchemeResponse> {
    const res = await apiClient.get<SchemeResponse>(`${ADMIN_BASE}/${id}`);
    return res.data;
  },

  async getTranslationStatus(id: string): Promise<TranslationStatusResponse> {
    const res = await apiClient.get<TranslationStatusResponse>(`${BASE}/${id}/translation-status`);
    return res.data;
  },

  async getAuditHistory(id: string, limit = 50): Promise<AuditHistoryResponse> {
    const res = await apiClient.get<AuditHistoryResponse>(`${BASE}/${id}/audit-history`, { params: { limit } });
    return res.data;
  },
};
