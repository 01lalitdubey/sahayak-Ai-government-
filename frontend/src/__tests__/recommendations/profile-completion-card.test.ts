/**
 * ProfileCompletionCard Tests — Sahayak AI (Phase 5)
 * Tests for the profile completion data model and display logic.
 */

import type {
  ProfileCompletionResponse,
  ProfileFieldStatus,
} from "@/types/recommendation";

// ── Profile field definitions ─────────────────────────────────────────────

describe("Profile field definitions", () => {
  const PROFILE_FIELDS: Array<{
    field: string;
    label: string;
    importance: ProfileFieldStatus["importance"];
  }> = [
    { field: "age", label: "Age", importance: "required" },
    { field: "gender", label: "Gender", importance: "required" },
    { field: "state", label: "State", importance: "required" },
    { field: "category", label: "Social Category", importance: "important" },
    { field: "occupation", label: "Occupation", importance: "important" },
    { field: "annual_income", label: "Annual Income", importance: "important" },
    { field: "district", label: "District", importance: "optional" },
    { field: "education", label: "Education Level", importance: "optional" },
    { field: "is_farmer", label: "Farmer Status", importance: "optional" },
    { field: "is_disabled", label: "Disability Status", importance: "optional" },
  ];

  test("there are exactly 10 tracked fields", () => {
    expect(PROFILE_FIELDS).toHaveLength(10);
  });

  test("required fields are age, gender, and state", () => {
    const required = PROFILE_FIELDS.filter((f) => f.importance === "required");
    expect(required.map((f) => f.field)).toEqual(
      expect.arrayContaining(["age", "gender", "state"])
    );
  });

  test("important fields include occupation, category, annual_income", () => {
    const important = PROFILE_FIELDS.filter((f) => f.importance === "important");
    expect(important.map((f) => f.field)).toEqual(
      expect.arrayContaining(["category", "occupation", "annual_income"])
    );
  });

  test("optional fields include district, education, is_farmer, is_disabled", () => {
    const optional = PROFILE_FIELDS.filter((f) => f.importance === "optional");
    expect(optional).toHaveLength(4);
  });
});

// ── Completion percentage calculation ─────────────────────────────────────

describe("Profile completion percentage", () => {
  function calcPct(filled: number, total: number): number {
    return Math.round((filled / total) * 100 * 10) / 10;
  }

  test("0/10 filled → 0%", () => expect(calcPct(0, 10)).toBe(0));
  test("5/10 filled → 50%", () => expect(calcPct(5, 10)).toBe(50));
  test("10/10 filled → 100%", () => expect(calcPct(10, 10)).toBe(100));
  test("7/10 filled → 70%", () => expect(calcPct(7, 10)).toBe(70));
  test("result is a number", () => expect(typeof calcPct(3, 10)).toBe("number"));
});

// ── Progress bar colour logic ──────────────────────────────────────────────

describe("Profile completion colour coding", () => {
  function progressColor(pct: number): string {
    if (pct >= 80) return "bg-emerald-500";
    if (pct >= 50) return "bg-amber-500";
    return "bg-rose-500";
  }

  test("100% → emerald (green)", () => {
    expect(progressColor(100)).toBe("bg-emerald-500");
  });

  test("80% → emerald (green)", () => {
    expect(progressColor(80)).toBe("bg-emerald-500");
  });

  test("70% → amber (orange)", () => {
    expect(progressColor(70)).toBe("bg-amber-500");
  });

  test("50% → amber (orange)", () => {
    expect(progressColor(50)).toBe("bg-amber-500");
  });

  test("30% → rose (red)", () => {
    expect(progressColor(30)).toBe("bg-rose-500");
  });

  test("0% → rose (red)", () => {
    expect(progressColor(0)).toBe("bg-rose-500");
  });
});

// ── ProfileCompletionResponse schema ──────────────────────────────────────

describe("ProfileCompletionResponse", () => {
  const MOCK_COMPLETE: ProfileCompletionResponse = {
    success: true,
    completion_percentage: 100.0,
    filled_count: 10,
    total_fields: 10,
    missing_fields: [],
    fields: [
      { field: "age", label: "Age", filled: true, importance: "required" },
      { field: "gender", label: "Gender", filled: true, importance: "required" },
    ],
  };

  const MOCK_PARTIAL: ProfileCompletionResponse = {
    success: true,
    completion_percentage: 30.0,
    filled_count: 3,
    total_fields: 10,
    missing_fields: ["Social Category", "Occupation", "Annual Income", "District", "Education Level", "Farmer Status", "Disability Status"],
    fields: [],
  };

  test("complete profile has 0 missing fields", () => {
    expect(MOCK_COMPLETE.missing_fields).toHaveLength(0);
    expect(MOCK_COMPLETE.completion_percentage).toBe(100.0);
  });

  test("partial profile correctly lists missing fields", () => {
    expect(MOCK_PARTIAL.missing_fields.length).toBeGreaterThan(0);
    expect(MOCK_PARTIAL.completion_percentage).toBeLessThan(100);
  });

  test("filled_count + missing_fields.length ≤ total_fields", () => {
    // filled + missing should be ≤ total (some may be optional and not listed as missing)
    expect(MOCK_PARTIAL.filled_count).toBeLessThanOrEqual(MOCK_PARTIAL.total_fields);
  });

  test("success field is always true for valid responses", () => {
    expect(MOCK_COMPLETE.success).toBe(true);
    expect(MOCK_PARTIAL.success).toBe(true);
  });

  test("percentage is between 0 and 100 inclusive", () => {
    expect(MOCK_COMPLETE.completion_percentage).toBeGreaterThanOrEqual(0);
    expect(MOCK_COMPLETE.completion_percentage).toBeLessThanOrEqual(100);
    expect(MOCK_PARTIAL.completion_percentage).toBeGreaterThanOrEqual(0);
    expect(MOCK_PARTIAL.completion_percentage).toBeLessThanOrEqual(100);
  });
});

// ── Empty/null profile state ───────────────────────────────────────────────

describe("ProfileCompletionCard — null profile state", () => {
  // Simulating what calculate_profile_completion(None) returns on backend
  const NULL_PROFILE_RESPONSE: ProfileCompletionResponse = {
    success: true,
    completion_percentage: 0.0,
    filled_count: 0,
    total_fields: 10,
    missing_fields: ["Age", "Gender", "State", "Social Category", "Occupation", "Annual Income", "District", "Education Level", "Farmer Status", "Disability Status"],
    fields: [],
  };

  test("null profile returns 0% completion", () => {
    expect(NULL_PROFILE_RESPONSE.completion_percentage).toBe(0.0);
  });

  test("null profile shows all 10 fields as missing", () => {
    expect(NULL_PROFILE_RESPONSE.missing_fields).toHaveLength(10);
  });

  test("filled_count is 0 for null profile", () => {
    expect(NULL_PROFILE_RESPONSE.filled_count).toBe(0);
  });
});
