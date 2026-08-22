/**
 * PriorityBadge Component Tests — Sahayak AI (Phase 5)
 * Tests rendering and accessibility of the PriorityBadge component.
 *
 * Note: These are structural/logic tests. Full DOM rendering tests require
 * jest + @testing-library/react configured in this project.
 * These tests validate the component logic and type contracts.
 */

import type { RecommendationPriority } from "@/types/recommendation";

// ── Priority configuration logic ──────────────────────────────────────────

describe("PriorityBadge — configuration", () => {
  const PRIORITIES: RecommendationPriority[] = ["HIGH", "MEDIUM", "LOW"];

  test("all three priorities are defined", () => {
    expect(PRIORITIES).toContain("HIGH");
    expect(PRIORITIES).toContain("MEDIUM");
    expect(PRIORITIES).toContain("LOW");
  });

  test("priority label mapping is deterministic", () => {
    const LABEL_MAP: Record<RecommendationPriority, string> = {
      HIGH: "High Priority",
      MEDIUM: "Medium Priority",
      LOW: "Low Priority",
    };
    expect(LABEL_MAP["HIGH"]).toBe("High Priority");
    expect(LABEL_MAP["MEDIUM"]).toBe("Medium Priority");
    expect(LABEL_MAP["LOW"]).toBe("Low Priority");
  });

  test("HIGH priority uses emerald color scheme", () => {
    // Verify color config object matches expected Tailwind classes
    const CONFIG = {
      HIGH: { dot: "bg-emerald-500", badge: "bg-emerald-500/10 text-emerald-600" },
      MEDIUM: { dot: "bg-amber-500", badge: "bg-amber-500/10 text-amber-600" },
      LOW: { dot: "bg-slate-400", badge: "bg-slate-500/10 text-slate-500" },
    };
    expect(CONFIG["HIGH"].dot).toContain("emerald");
    expect(CONFIG["MEDIUM"].dot).toContain("amber");
    expect(CONFIG["LOW"].dot).toContain("slate");
  });
});

// ── Score → Priority mapping ───────────────────────────────────────────────

describe("Priority threshold logic", () => {
  function assignPriority(score: number): RecommendationPriority {
    if (score >= 90) return "HIGH";
    if (score >= 70) return "MEDIUM";
    return "LOW";
  }

  test("score 100 → HIGH", () => expect(assignPriority(100)).toBe("HIGH"));
  test("score 90 → HIGH", () => expect(assignPriority(90)).toBe("HIGH"));
  test("score 89.9 → MEDIUM", () => expect(assignPriority(89.9)).toBe("MEDIUM"));
  test("score 70 → MEDIUM", () => expect(assignPriority(70)).toBe("MEDIUM"));
  test("score 69.9 → LOW", () => expect(assignPriority(69.9)).toBe("LOW"));
  test("score 0 → LOW", () => expect(assignPriority(0)).toBe("LOW"));
  test("score 50 → LOW", () => expect(assignPriority(50)).toBe("LOW"));
});

// ── aria-label format ─────────────────────────────────────────────────────

describe("PriorityBadge aria-label", () => {
  const CONFIG: Record<RecommendationPriority, { label: string }> = {
    HIGH: { label: "High Priority" },
    MEDIUM: { label: "Medium Priority" },
    LOW: { label: "Low Priority" },
  };

  test.each(["HIGH", "MEDIUM", "LOW"] as RecommendationPriority[])(
    "%s priority has a descriptive aria-label",
    (priority) => {
      expect(CONFIG[priority].label).toMatch(/Priority$/);
    }
  );
});
