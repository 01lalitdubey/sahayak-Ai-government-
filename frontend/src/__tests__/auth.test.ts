/**
 * Frontend Auth Tests — Sahayak AI
 * Structural / type-level tests (no require() calls).
 * Runtime tests require a test runner with jsdom (e.g. vitest + @testing-library).
 */

import { TOKEN_KEYS } from "@/types/auth";
import type { AuthUser } from "@/types/auth";

// ── TOKEN_KEYS ────────────────────────────────────────────────────────────

describe("TOKEN_KEYS", () => {
  test("has expected storage key names", () => {
    expect(TOKEN_KEYS.ACCESS).toBe("sahayak_access_token");
    expect(TOKEN_KEYS.REFRESH).toBe("sahayak_refresh_token");
    expect(TOKEN_KEYS.USER).toBe("sahayak_user");
  });
});

// ── AuthUser type shape ───────────────────────────────────────────────────

describe("AuthUser type", () => {
  test("user object satisfies AuthUser shape", () => {
    const user: AuthUser = {
      id: "abc-123",
      email: "ravi@example.com",
      full_name: "Ravi Kumar",
      role: "user",
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    expect(user.role).toBe("user");
    expect(user.is_active).toBe(true);
  });

  test("admin role is valid", () => {
    const role: AuthUser["role"] = "admin";
    expect(role).toBe("admin");
  });

  test("super_admin role is valid", () => {
    const role: AuthUser["role"] = "super_admin";
    expect(role).toBe("super_admin");
  });
});
