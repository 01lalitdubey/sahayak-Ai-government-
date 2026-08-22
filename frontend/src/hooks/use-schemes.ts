/**
 * Scheme React Query Hooks — Sahayak AI
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { schemeService } from "@/services/scheme.service";
import type {
  SchemeFilters,
  AdminSchemeFilters,
  SchemeCreatePayload,
  SchemeUpdatePayload,
} from "@/types/scheme";
import { useLocale } from "next-intl";

export const SCHEME_KEYS = {
  all: ["schemes"] as const,
  lists: (locale: string) => [...SCHEME_KEYS.all, "list", locale] as const,
  list: (locale: string, filters: Partial<SchemeFilters>) => [...SCHEME_KEYS.lists(locale), filters] as const,
  details: (locale: string) => [...SCHEME_KEYS.all, "detail", locale] as const,
  detail: (locale: string, id: string) => [...SCHEME_KEYS.details(locale), id] as const,
  featured: (locale: string) => [...SCHEME_KEYS.all, "featured", locale] as const,
  recent: (locale: string) => [...SCHEME_KEYS.all, "recent", locale] as const,
  categories: (locale: string) => [...SCHEME_KEYS.all, "categories", locale] as const,
  states: (locale: string) => [...SCHEME_KEYS.all, "states", locale] as const,
  // Admin keys
  adminList: (filters: Partial<AdminSchemeFilters>) => ["admin", "schemes", "list", filters] as const,
  adminDetail: (id: string) => ["admin", "schemes", "detail", id] as const,
  translationStatus: (id: string) => ["admin", "schemes", "translation-status", id] as const,
  auditHistory: (id: string) => ["admin", "schemes", "audit-history", id] as const,
};

// ── Public Hooks ────────────────────────────────────────────────────────────

export function useSchemes(filters: Partial<SchemeFilters> = {}) {
  const locale = useLocale();
  return useQuery({
    queryKey: SCHEME_KEYS.list(locale, filters),
    queryFn: () => schemeService.getSchemes(filters),
    staleTime: 1000 * 60 * 2,
    placeholderData: (prev) => prev,
  });
}

export function useScheme(id: string | null) {
  const locale = useLocale();
  return useQuery({
    queryKey: SCHEME_KEYS.detail(locale, id ?? ""),
    queryFn: () => schemeService.getScheme(id!),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}

export function useSchemeByCode(code: string | null) {
  const locale = useLocale();
  return useQuery({
    queryKey: SCHEME_KEYS.detail(locale, code ?? ""),
    queryFn: () => schemeService.getSchemeByCode(code!),
    enabled: !!code,
    staleTime: 1000 * 60 * 5,
  });
}

export function useFeaturedSchemes(limit = 6) {
  const locale = useLocale();
  return useQuery({
    queryKey: SCHEME_KEYS.featured(locale),
    queryFn: () => schemeService.getFeatured(limit),
    staleTime: 1000 * 60 * 10,
  });
}

export function useRecentSchemes(limit = 6) {
  const locale = useLocale();
  return useQuery({
    queryKey: SCHEME_KEYS.recent(locale),
    queryFn: () => schemeService.getRecent(limit),
    staleTime: 1000 * 60 * 5,
  });
}

export function useCategories() {
  const locale = useLocale();
  return useQuery({
    queryKey: SCHEME_KEYS.categories(locale),
    queryFn: () => schemeService.getCategories(),
    staleTime: Infinity,
  });
}

export function useStates() {
  const locale = useLocale();
  return useQuery({
    queryKey: SCHEME_KEYS.states(locale),
    queryFn: () => schemeService.getStates(),
    staleTime: Infinity,
  });
}

// ── Admin Hooks ─────────────────────────────────────────────────────────────

export function useAdminSchemes(filters: Partial<AdminSchemeFilters> = {}) {
  return useQuery({
    queryKey: SCHEME_KEYS.adminList(filters),
    queryFn: () => schemeService.getAdminSchemes(filters),
    staleTime: 1000 * 30,
    placeholderData: (prev) => prev,
  });
}

export function useAdminScheme(id: string | null) {
  return useQuery({
    queryKey: SCHEME_KEYS.adminDetail(id ?? ""),
    queryFn: () => schemeService.getAdminScheme(id!),
    enabled: !!id,
    staleTime: 1000 * 60,
  });
}

export function useSchemeTranslationStatus(id: string | null) {
  return useQuery({
    queryKey: SCHEME_KEYS.translationStatus(id ?? ""),
    queryFn: () => schemeService.getTranslationStatus(id!),
    enabled: !!id,
    staleTime: 1000 * 30,
    refetchInterval: 1000 * 30, // Poll every 30s to show processing → published
  });
}

export function useSchemeAuditHistory(id: string | null) {
  return useQuery({
    queryKey: SCHEME_KEYS.auditHistory(id ?? ""),
    queryFn: () => schemeService.getAuditHistory(id!),
    enabled: !!id,
    staleTime: 1000 * 60,
  });
}

// ── Mutation Hooks ──────────────────────────────────────────────────────────

export function useCreateScheme() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SchemeCreatePayload) => schemeService.createScheme(payload),
    onSuccess: () => {
      // Invalidate both public and admin lists
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.all });
      qc.invalidateQueries({ queryKey: ["admin", "schemes"] });
    },
  });
}

export function useUpdateScheme(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SchemeUpdatePayload) => schemeService.updateScheme(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.all });
      qc.invalidateQueries({ queryKey: ["admin", "schemes"] });
      // Also invalidate translation status since content may have changed
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.translationStatus(id) });
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.auditHistory(id) });
    },
  });
}

export function usePublishScheme() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      schemeService.updateStatus(id, is_active),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.all });
      qc.invalidateQueries({ queryKey: ["admin", "schemes"] });
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.translationStatus(id) });
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.auditHistory(id) });
    },
  });
}

export function useArchiveScheme() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => schemeService.deleteScheme(id),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.all });
      qc.invalidateQueries({ queryKey: ["admin", "schemes"] });
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.auditHistory(id) });
    },
  });
}

export function useRestoreScheme() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => schemeService.restoreScheme(id),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.all });
      qc.invalidateQueries({ queryKey: ["admin", "schemes"] });
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.translationStatus(id) });
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.auditHistory(id) });
    },
  });
}

// Legacy compatibility aliases
export function useDeleteScheme() {
  return useArchiveScheme();
}

export function useUpdateStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      schemeService.updateStatus(id, is_active),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: SCHEME_KEYS.all });
      qc.invalidateQueries({ queryKey: ["admin", "schemes"] });
    },
  });
}
