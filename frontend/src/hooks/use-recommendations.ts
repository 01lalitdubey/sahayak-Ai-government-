/**
 * Recommendation React Query Hooks — Sahayak AI (Phase 5)
 * Caching, background refresh, and optimistic invalidation.
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { showToast } from "@/components/ui/toast-utils";
import { recommendationService } from "@/services/recommendation.service";
import type { RecommendationFilters } from "@/types/recommendation";
import { useLocale } from "next-intl";

// ── Query key factory ─────────────────────────────────────────────────────

export const RECOMMENDATION_KEYS = {
  all: ["recommendations"] as const,
  lists: (locale: string) => [...RECOMMENDATION_KEYS.all, "list", locale] as const,
  list: (locale: string, filters: Partial<RecommendationFilters>) =>
    [...RECOMMENDATION_KEYS.lists(locale), filters] as const,
  details: (locale: string) => [...RECOMMENDATION_KEYS.all, "detail", locale] as const,
  detail: (locale: string, id: string) => [...RECOMMENDATION_KEYS.details(locale), id] as const,
  top: (locale: string) => [...RECOMMENDATION_KEYS.all, "top", locale] as const,
  profile: (locale: string) => [...RECOMMENDATION_KEYS.all, "profile", locale] as const,
};

// ── Hooks ─────────────────────────────────────────────────────────────────

export function useRecommendations(filters: Partial<RecommendationFilters> = {}) {
  const locale = useLocale();
  return useQuery({
    queryKey: RECOMMENDATION_KEYS.list(locale, filters),
    queryFn: () => recommendationService.getRecommendations(filters),
    staleTime: 1000 * 60 * 3, // 3 minutes
    placeholderData: (prev) => prev,
    retry: (failureCount, error: unknown) => {
      // Don't retry on 422 (profile incomplete) or 401 (unauthorized)
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 422 || status === 401) return false;
      return failureCount < 2;
    },
  });
}

export function useTopRecommendations(limit = 5) {
  const locale = useLocale();
  return useQuery({
    queryKey: RECOMMENDATION_KEYS.top(locale),
    queryFn: () => recommendationService.getTopRecommendations(limit),
    staleTime: 1000 * 60 * 5, // 5 minutes
    // Never throw — dashboard shows graceful empty state
    retry: false,
  });
}

export function useRecommendation(schemeId: string | null) {
  const locale = useLocale();
  return useQuery({
    queryKey: RECOMMENDATION_KEYS.detail(locale, schemeId ?? ""),
    queryFn: () => recommendationService.getRecommendation(schemeId!),
    enabled: !!schemeId,
    staleTime: 1000 * 60 * 5,
  });
}

export function useProfileCompletion() {
  const locale = useLocale();
  return useQuery({
    queryKey: RECOMMENDATION_KEYS.profile(locale),
    queryFn: () => recommendationService.getProfileCompletion(),
    staleTime: 1000 * 60 * 2,
  });
}

export function useRefreshRecommendations() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => recommendationService.refreshRecommendations(),
    onSuccess: (data) => {
      // Invalidate all recommendation queries so they refetch
      qc.invalidateQueries({ queryKey: RECOMMENDATION_KEYS.all });
      showToast(
        `Recommendations refreshed — ${data.total_recommendations} results found.`,
        "success"
      );
    },
    onError: () => {
      showToast("Failed to refresh recommendations. Please try again.", "error");
    },
  });
}
