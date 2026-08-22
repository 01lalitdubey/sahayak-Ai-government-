export type EligibilityStatus = "eligible" | "not_eligible" | "incomplete_profile" | "no_rules";

export interface RuleResult {
  criterion: string;
  requirement: string;
  user_value: string;
  passed: boolean;
  reason: string;
}

export interface EligibilityCheckResponse {
  scheme_id: string;
  scheme_name: string;
  scheme_code: string;
  eligible: boolean;
  status: EligibilityStatus;
  score: number;
  total_rules: number;
  passed_count: number;
  failed_count: number;
  missing_count: number;
  passed_rules: RuleResult[];
  failed_rules: RuleResult[];
  missing_information: string[];
  recommendations: string[];
  evaluated_at: string;
}

export interface EligibilitySummary {
  scheme_id: string;
  scheme_name: string;
  scheme_code: string;
  scheme_type: string;
  category: string | null;
  ministry: string | null;
  state: string | null;
  eligible: boolean;
  status: EligibilityStatus;
  score: number;
  total_rules: number;
  passed_count: number;
}

export interface MySchemeEligibilityResponse {
  success: boolean;
  message: string;
  total_schemes: number;
  eligible_count: number;
  not_eligible_count: number;
  incomplete_count: number;
  profile_completion: number;
  data: EligibilitySummary[];
}

export interface EligibilityRuleAdmin {
  id: string;
  scheme_id: string;
  minimum_age: number | null;
  maximum_age: number | null;
  minimum_income: number | null;
  maximum_income: number | null;
  gender: string | null;
  occupation: string | null;
  state: string | null;
  category: string | null;
  education: string | null;
  require_farmer: boolean | null;
  require_disabled: boolean | null;
  created_at: string;
  updated_at: string;
}

export interface EligibilityRuleCreatePayload {
  scheme_id: string;
  minimum_age?: number;
  maximum_age?: number;
  minimum_income?: number;
  maximum_income?: number;
  gender?: string;
  occupation?: string;
  state?: string;
  category?: string;
  education?: string;
  require_farmer?: boolean;
  require_disabled?: boolean;
}
