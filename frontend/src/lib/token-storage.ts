/**
 * Token Storage — Sahayak AI
 * Centralised localStorage access for auth tokens.
 * All token read/write goes through here — never scattered across components.
 * Guards against SSR (no window object on server).
 */

import { TOKEN_KEYS, type AuthUser } from "@/types/auth";

const isBrowser = typeof window !== "undefined";

export const tokenStorage = {
  // ── Access token ────────────────────────────────────────────────────────
  getAccessToken(): string | null {
    if (!isBrowser) return null;
    return localStorage.getItem(TOKEN_KEYS.ACCESS);
  },
  setAccessToken(token: string): void {
    if (!isBrowser) return;
    localStorage.setItem(TOKEN_KEYS.ACCESS, token);
  },
  removeAccessToken(): void {
    if (!isBrowser) return;
    localStorage.removeItem(TOKEN_KEYS.ACCESS);
  },

  // ── Refresh token ───────────────────────────────────────────────────────
  getRefreshToken(): string | null {
    if (!isBrowser) return null;
    return localStorage.getItem(TOKEN_KEYS.REFRESH);
  },
  setRefreshToken(token: string): void {
    if (!isBrowser) return;
    localStorage.setItem(TOKEN_KEYS.REFRESH, token);
  },
  removeRefreshToken(): void {
    if (!isBrowser) return;
    localStorage.removeItem(TOKEN_KEYS.REFRESH);
  },

  // ── User ────────────────────────────────────────────────────────────────
  getUser(): AuthUser | null {
    if (!isBrowser) return null;
    try {
      const raw = localStorage.getItem(TOKEN_KEYS.USER);
      return raw ? (JSON.parse(raw) as AuthUser) : null;
    } catch {
      return null;
    }
  },
  setUser(user: AuthUser): void {
    if (!isBrowser) return;
    localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user));
  },
  removeUser(): void {
    if (!isBrowser) return;
    localStorage.removeItem(TOKEN_KEYS.USER);
  },

  // ── Clear all ───────────────────────────────────────────────────────────
  clearAll(): void {
    if (!isBrowser) return;
    localStorage.removeItem(TOKEN_KEYS.ACCESS);
    localStorage.removeItem(TOKEN_KEYS.REFRESH);
    localStorage.removeItem(TOKEN_KEYS.USER);
    // Also clear Zustand persisted store key
    localStorage.removeItem("sahayak-auth");
  },
};
