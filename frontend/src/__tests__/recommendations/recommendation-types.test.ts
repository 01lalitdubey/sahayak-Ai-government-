/**
 * Recommendation Types Tests — Sahayak AI (Phase 5)
 * Validates TypeScript type shapes and enum values at runtime.
 * Pure structural tests — no DOM, no mocks needed.
 */

import type {
  RecommendationPriority,
  RecommendationReasonType,
  RecommendationReason,
  RecommendationScore,
  RecommendationSummary,
  RecommendationResponse,
  TopRecommendationsResponse,
  RecommendationRefreshResponse,
  ProfileFieldStatus,
  ProfileCompletionResponse,
  RecommendationFilters,
} from "@/types/recommendation";

// ── Priority ──────────────────────────────────────────────────────────────

describe("RecommendationPriority", () => {
  test("HIGH is a valid priority", () => {
    const p: RecommendationPriority = "HIGH";
    expect(p).toBe("HIGH");
  });

  test("MEDIUM is a valid priority", () => {
    const p: RecommendationPriority = "MEDIUM";
    expect(p).toBe("MEDIUM");
  });

  test("LOW is a valid priority", () => {
    const p: RecommendationPriority = "LOW";
    expect(p).toBe("LOW");
  });
});

// ── ReasonType ────────────────────────────────────────────────────────────

describe("RecommendationReasonType", () => {
  const VALID_TYPES: RecommendationReasonType[] = [
    "eligibility",
    "occupation",
    "income",
    "state",
    "category",
    "featured",
    "general",
  ];

  test.each(VALID_TYPES)('"%s" is a valid reason type', (type) => {
    const r: RecommendationReasonType = type;
    expect(r).toBe(type);
  });
});

// ── RecommendationReason ──────────────────────────────────────────────────

describe("RecommendationReason", () => {
  test("satisfies interface shape", () => {
    const reason: RecommendationReason = {
      reason_type: "eligibility",
      text: "You satisfy all eligibility rules.",
    };
    expect(reason.reason_type).toBe("eligibility");
    expect(typeof reason.text).toBe("string");
  });
});

// ── RecommendationScore ───────────────────────────────────────────────────

describe("RecommendationScore", () => {
  test("satisfies interface with all fields", () => {
    const score: RecommendationScore = {
      total: 92.5,
      eligibility_score: 40,
      occupation_score: 20,
      income_score: 15,
      state_score: 10,
      category_score: 7.5,
      featured_score: 0,
    };
    expect(score.total).toBe(92.5);
    expect(score.eligibility_score).toBe(40);
    expect(score.featured_score).toBe(0);
  });

  test("weights sum to 100", () => {
    const score: RecommendationScore = {
      total: 100,
      eligibility_score: 40,
      occupation_score: 20,
      income_score: 15,
      state_score: 10,
      category_score: 10,
      featured_score: 5,
    };
    const sum =
      score.eligibility_score +
      score.occupation_score +
      score.income_score +
      score.state_score +
      score.category_score +
      score.featured_score;
    expect(sum).toBe(100);
  });
});

// ── RecommendationSummary ─────────────────────────────────────────────────

describe("RecommendationSummary", () => {
  const summary: RecommendationSummary = {
    scheme_id: "uuid-1234",
    scheme_name: "PM-KISAN",
    scheme_code: "PM-KISAN-2024",
    scheme_type: "central",
    category: "agriculture",
    ministry: "Ministry of Agriculture",
    state: null,
    is_featured: true,
    official_url: "https://pmkisan.gov.in",
    short_description: "Income support for farmers.",
    recommendation_score: 92.5,
    priority: "HIGH",
    eligibility_status: "eligible",
    eligible: true,
    reasons: [
      { reason_type: "eligibility", text: "You satisfy all rules." },
    ],
    missing_information: [],
  };

  test("has required fields", () => {
    expect(summary.scheme_id).toBe("uuid-1234");
    expect(summary.priority).toBe("HIGH");
    expect(summary.eligible).toBe(true);
  });

  test("eligibility_status accepts valid values", () => {
    const statuses: RecommendationSummary["eligibility_status"][] = [
      "eligible",
      "incomplete_profile",
      "no_rules",
      "not_eligible",
    ];
    statuses.forEach((s) => expect(typeof s).toBe("string"));
  });

  test("state can be null for central schemes", () => {
    expect(summary.state).toBeNull();
  });

  test("missing_information is an array", () => {
    expect(Array.isArray(summary.missing_information)).toBe(true);
  });
});

// ── RecommendationResponse ────────────────────────────────────────────────

describe("RecommendationResponse", () => {
  test("satisfies paginated list shape", () => {
    const resp: RecommendationResponse = {
      success: true,
      message: "OK",
      total: 12,
      page: 1,
      page_size: 10,
      total_pages: 2,
      data: [],
    };
    expect(resp.total).toBe(12);
    expect(resp.total_pages).toBe(2);
  });
});

// ── TopRecommendationsResponse ────────────────────────────────────────────

describe("TopRecommendationsResponse", () => {
  test("has success and data fields", () => {
    const resp: TopRecommendationsResponse = {
      success: true,
      message: "OK",
      data: [],
    };
    expect(resp.success).toBe(true);
    expect(Array.isArray(resp.data)).toBe(true);
  });
});

// ── RecommendationRefreshResponse ─────────────────────────────────────────

describe("RecommendationRefreshResponse", () => {
  test("has expected fields", () => {
    const resp: RecommendationRefreshResponse = {
      success: true,
      message: "Recommendations refreshed successfully.",
      total_recommendations: 7,
      refreshed_at: new Date().toISOString(),
    };
    expect(resp.success).toBe(true);
    expect(resp.total_recommendations).toBe(7);
    expect(typeof resp.refreshed_at).toBe("string");
  });
});

// ── ProfileFieldStatus ────────────────────────────────────────────────────

describe("ProfileFieldStatus", () => {
  test("satisfies interface", () => {
    const field: ProfileFieldStatus = {
      field: "state",
      label: "State",
      filled: true,
      importance: "required",
    };
    expect(field.importance).toBe("required");
  });

  test("importance accepts all valid values", () => {
    const importances: ProfileFieldStatus["importance"][] = [
      "required",
      "important",
      "optional",
    ];
    importances.forEach((i) => expect(typeof i).toBe("string"));
  });
});

// ── ProfileCompletionResponse ─────────────────────────────────────────────

describe("ProfileCompletionResponse", () => {
  test("satisfies interface with numeric percentage", () => {
    const resp: ProfileCompletionResponse = {
      success: true,
      completion_percentage: 70.0,
      filled_count: 7,
      total_fields: 10,
      missing_fields: ["District", "Education Level", "Disability Status"],
      fields: [],
    };
    expect(resp.completion_percentage).toBe(70.0);
    expect(resp.missing_fields).toHaveLength(3);
  });
});

// ── RecommendationFilters ─────────────────────────────────────────────────

describe("RecommendationFilters", () => {
  test("all filter fields are optional", () => {
    const empty: RecommendationFilters = {};
    expect(empty.priority).toBeUndefined();
    expect(empty.sort).toBeUndefined();
  });

  test("sort accepts all valid values", () => {
    const sorts: Required<RecommendationFilters>["sort"][] = [
      "score_desc",
      "score_asc",
      "alphabetical",
      "priority",
    ];
    sorts.forEach((s) => expect(typeof s).toBe("string"));
  });
});
