/**
 * Recommendation Engine Types — Sahayak AI (Phase 5)
 * TypeScript types mirroring the backend Pydantic schemas.
 */

export type RecommendationPriority = "HIGH" | "MEDIUM" | "LOW";

export type RecommendationReasonType =
  | "eligibility"
  | "occupation"
  | "income"
  | "state"
  | "category"
  | "featured"
  | "general";

export interface RecommendationReason {
  reason_type: RecommendationReasonType;
  text: string;
}

export interface RecommendationScore {
  total: number;
  eligibility_score: number;
  occupation_score: number;
  income_score: number;
  state_score: number;
  category_score: number;
  featured_score: number;
}

export interface RecommendationSummary {
  scheme_id: string;
  scheme_name: string;
  scheme_code: string;
  scheme_type: string;
  category: string | null;
  ministry: string | null;
  state: string | null;
  is_featured: boolean;
  official_url: string | null;
  short_description: string | null;
  recommendation_score: number;
  priority: RecommendationPriority;
  eligibility_status: "eligible" | "incomplete_profile" | "no_rules" | "not_eligible";
  eligible: boolean;
  reasons: RecommendationReason[];
  missing_information: string[];
}

export interface RecommendationDetail extends RecommendationSummary {
  score_breakdown: RecommendationScore;
  ministry: string | null;
  department: string | null;
  official_pdf_url: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  full_description: string | null;
  benefits: string | null;
  application_mode: string;
  application_start_date: string | null;
  application_end_date: string | null;
  passed_rules: Array<{
    criterion: string;
    requirement: string;
    user_value: string;
    passed: boolean;
    reason: string;
  }>;
  failed_rules: Array<{
    criterion: string;
    requirement: string;
    user_value: string;
    passed: boolean;
    reason: string;
  }>;
  evaluated_at: string;
}

export interface RecommendationResponse {
  success: boolean;
  message: string;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  data: RecommendationSummary[];
}

export interface TopRecommendationsResponse {
  success: boolean;
  message: string;
  data: RecommendationSummary[];
}

export interface RecommendationRefreshResponse {
  success: boolean;
  message: string;
  total_recommendations: number;
  refreshed_at: string;
}

export interface ProfileFieldStatus {
  field: string;
  label: string;
  filled: boolean;
  importance: "required" | "important" | "optional";
}

export interface ProfileCompletionResponse {
  success: boolean;
  completion_percentage: number;
  filled_count: number;
  total_fields: number;
  missing_fields: string[];
  fields: ProfileFieldStatus[];
}

export interface RecommendationFilters {
  priority?: RecommendationPriority;
  category?: string;
  sort?: "score_desc" | "score_asc" | "alphabetical" | "priority";
  page?: number;
  page_size?: number;
}
