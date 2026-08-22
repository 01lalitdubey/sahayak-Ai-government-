/**
 * Scheme Types — Sahayak AI
 * Matches backend Pydantic schemas exactly.
 */

export type SchemeType = "central" | "state";
export type ApplicationMode = "online" | "offline" | "both";
export type SchemeCategory =
  | "agriculture" | "education" | "health" | "housing" | "women_and_child"
  | "social_welfare" | "financial_inclusion" | "skill_development"
  | "rural_development" | "pension" | "insurance" | "employment"
  | "disability" | "minority" | "farmer" | "student" | "women"
  | "healthcare" | "business" | "tribal" | "transport" | "finance" | "other";

export type SortOption = "newest" | "oldest" | "alphabetical" | "most_viewed" | "recently_updated";

export type TranslationStatusValue = "published" | "outdated" | "processing" | "missing";

export interface SchemeSummary {
  id: string;
  scheme_code: string;
  name: string;
  short_description: string | null;
  scheme_type: SchemeType;
  category: SchemeCategory | null;
  ministry: string | null;
  state: string | null;
  application_mode: ApplicationMode;
  application_end_date: string | null;
  is_active: boolean;
  is_featured: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
}

export interface SchemeDetail extends SchemeSummary {
  full_description: string | null;
  benefits: string | null;
  required_documents: string | null;
  application_process: string | null;
  department: string | null;
  district: string | null;
  application_start_date: string | null;
  official_url: string | null;
  official_pdf_url: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  created_by: string | null;
  updated_by: string | null;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SchemeListResponse {
  success: boolean;
  message: string;
  data: SchemeSummary[];
  meta: PaginationMeta;
}

export interface SchemeResponse {
  success: boolean;
  message: string;
  data: SchemeDetail | null;
}

export interface CategoryItem {
  value: SchemeCategory;
  label: string;
}

export interface CategoriesResponse {
  success: boolean;
  data: CategoryItem[];
}

export interface StatesResponse {
  success: boolean;
  data: string[];
}

export interface SchemeFilters {
  query?: string;
  category?: SchemeCategory | "";
  scheme_type?: SchemeType | "";
  application_mode?: ApplicationMode | "";
  state?: string;
  ministry?: string;
  is_featured?: boolean | null;
  is_active?: boolean | null;
  sort: SortOption;
  page: number;
  page_size: number;
}

export interface AdminSchemeFilters extends SchemeFilters {
  is_active?: boolean | null; // null = all (draft + published + archived)
}

export interface SchemeCreatePayload {
  scheme_code: string;
  name: string;
  short_description?: string;
  full_description?: string;
  benefits?: string;
  required_documents?: string;
  application_process?: string;
  scheme_type: SchemeType;
  category?: SchemeCategory | "";
  ministry?: string;
  department?: string;
  state?: string;
  district?: string;
  application_mode: ApplicationMode;
  application_start_date?: string;
  application_end_date?: string;
  official_url?: string;
  official_pdf_url?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
  is_featured: boolean;
}

export type SchemeUpdatePayload = Partial<Omit<SchemeCreatePayload, "scheme_code">>;

// ── Translation Status ──────────────────────────────────────────────────────

export interface TranslationStatusItem {
  language_code: string;
  language_name: string;
  status: TranslationStatusValue;
  is_published: boolean;
  version: number | null;
  updated_at: string | null;
  review_status: string | null;
}

export interface TranslationStatusResponse {
  scheme_id: string;
  scheme_code: string;
  source_language: string;
  translations: TranslationStatusItem[];
}

// ── Audit History ───────────────────────────────────────────────────────────

export interface AuditHistoryItem {
  id: string;
  action: string;
  admin_email: string | null;
  admin_name: string | null;
  result: string | null;
  details: Record<string, unknown> | null;
  timestamp: string;
}

export interface AuditHistoryResponse {
  scheme_id: string;
  scheme_code: string;
  events: AuditHistoryItem[];
  total: number;
}

// ── Sort and page options ───────────────────────────────────────────────────

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "newest", label: "Newest First" },
  { value: "oldest", label: "Oldest First" },
  { value: "alphabetical", label: "A → Z" },
  { value: "most_viewed", label: "Most Viewed" },
  { value: "recently_updated", label: "Recently Updated" },
];

export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];
