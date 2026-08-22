import apiClient from "@/lib/axios";
import type {
  EligibilityCheckResponse,
  MySchemeEligibilityResponse,
  EligibilityRuleAdmin,
  EligibilityRuleCreatePayload,
} from "@/types/eligibility";

const BASE = "/api/v1/eligibility";

export const eligibilityService = {
  async checkEligibility(scheme_id: string): Promise<EligibilityCheckResponse> {
    const res = await apiClient.post<EligibilityCheckResponse>(`${BASE}/check`, { scheme_id });
    return res.data;
  },

  async getMySchemes(): Promise<MySchemeEligibilityResponse> {
    const res = await apiClient.get<MySchemeEligibilityResponse>(`${BASE}/my-schemes`);
    return res.data;
  },

  async getEligibility(scheme_id: string): Promise<EligibilityCheckResponse> {
    const res = await apiClient.get<EligibilityCheckResponse>(`${BASE}/${scheme_id}`);
    return res.data;
  },

  async getRules(scheme_id?: string): Promise<{ data: EligibilityRuleAdmin[]; total: number }> {
    const params = scheme_id ? { scheme_id } : {};
    const res = await apiClient.get(`${BASE}/admin/rules`, { params });
    return res.data;
  },

  async createRule(payload: EligibilityRuleCreatePayload): Promise<{ data: EligibilityRuleAdmin }> {
    const res = await apiClient.post(`${BASE}/admin/rules`, payload);
    return res.data;
  },

  async updateRule(id: string, payload: Partial<EligibilityRuleCreatePayload>): Promise<{ data: EligibilityRuleAdmin }> {
    const res = await apiClient.put(`${BASE}/admin/rules/${id}`, payload);
    return res.data;
  },

  async deleteRule(id: string): Promise<void> {
    await apiClient.delete(`${BASE}/admin/rules/${id}`);
  },
};
