/**
 * Recommendation Service — Sahayak AI (Phase 5)
 * All HTTP calls to /api/v1/recommendations/* go through here.
 */

import apiClient from "@/lib/axios";
import type {
  RecommendationResponse,
  TopRecommendationsResponse,
  RecommendationDetail,
  RecommendationRefreshResponse,
  ProfileCompletionResponse,
  RecommendationFilters,
} from "@/types/recommendation";

const BASE = "/api/v1/recommendations";

export const recommendationService = {
  async getRecommendations(
    filters: Partial<RecommendationFilters> = {}
  ): Promise<RecommendationResponse> {
    const params: Record<string, string> = {};
    if (filters.priority) params["priority"] = filters.priority;
    if (filters.category) params["category"] = filters.category;
    if (filters.sort) params["sort"] = filters.sort;
    if (filters.page) params["page"] = String(filters.page);
    if (filters.page_size) params["page_size"] = String(filters.page_size);
    const res = await apiClient.get<RecommendationResponse>(BASE, { params });
    return res.data;
  },

  async getTopRecommendations(limit = 5): Promise<TopRecommendationsResponse> {
    const res = await apiClient.get<TopRecommendationsResponse>(`${BASE}/top`, {
      params: { limit },
    });
    return res.data;
  },

  async getRecommendation(schemeId: string): Promise<RecommendationDetail> {
    const res = await apiClient.get<RecommendationDetail>(`${BASE}/${schemeId}`);
    return res.data;
  },

  async refreshRecommendations(): Promise<RecommendationRefreshResponse> {
    const res = await apiClient.post<RecommendationRefreshResponse>(`${BASE}/refresh`);
    return res.data;
  },

  async getProfileCompletion(): Promise<ProfileCompletionResponse> {
    const res = await apiClient.get<ProfileCompletionResponse>(`${BASE}/profile`);
    return res.data;
  },
};
