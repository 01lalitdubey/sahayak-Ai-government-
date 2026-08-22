/**
 * Auth Store — Sahayak AI (Zustand)
 * Production-ready store replacing the Phase 1 placeholder.
 * Tokens are persisted in localStorage via tokenStorage.
 * Zustand state holds the runtime view — tokenStorage is the source of truth on reload.
 */

"use client";

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { tokenStorage } from "@/lib/token-storage";
import { authService } from "@/services/auth.service";
import type { AuthUser } from "@/types/auth";

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (accessToken: string, refreshToken: string, user: AuthUser) => void;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
  restoreSession: () => Promise<void>;
  clearSession: () => void;
  updateUser: (user: AuthUser) => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true, // true on mount until restoreSession completes

      // ── Login ─────────────────────────────────────────────────────────
      login(accessToken, refreshToken, user) {
        tokenStorage.setAccessToken(accessToken);
        tokenStorage.setRefreshToken(refreshToken);
        tokenStorage.setUser(user);
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      // ── Logout ────────────────────────────────────────────────────────
      async logout() {
        try {
          // Best-effort server-side logout (stateless — just informational)
          await authService.logout();
        } catch {
          // Ignore — we clear locally regardless
        } finally {
          get().clearSession();
        }
      },

      // ── Refresh tokens ────────────────────────────────────────────────
      async refresh() {
        const storedRefresh = tokenStorage.getRefreshToken();
        if (!storedRefresh) {
          get().clearSession();
          return false;
        }
        try {
          const res = await authService.refresh(storedRefresh);
          tokenStorage.setAccessToken(res.access_token);
          tokenStorage.setRefreshToken(res.refresh_token);
          set({
            accessToken: res.access_token,
            refreshToken: res.refresh_token,
          });
          return true;
        } catch {
          get().clearSession();
          return false;
        }
      },

      // ── Restore session on page reload ────────────────────────────────
      async restoreSession() {
        set({ isLoading: true });
        const storedToken = tokenStorage.getAccessToken();
        const storedUser = tokenStorage.getUser();

        if (!storedToken || !storedUser) {
          set({ isLoading: false });
          return;
        }

        try {
          // Verify token is still valid by calling /me
          const res = await authService.me();
          if (res.success && res.data) {
            tokenStorage.setUser(res.data);
            set({
              user: res.data,
              accessToken: storedToken,
              refreshToken: tokenStorage.getRefreshToken(),
              isAuthenticated: true,
            });
          } else {
            get().clearSession();
          }
        } catch (err: unknown) {
          // 401 — token expired, try refresh
          const status = (err as { response?: { status?: number } })?.response?.status;
          if (status === 401) {
            const refreshed = await get().refresh();
            if (refreshed) {
              try {
                const res2 = await authService.me();
                if (res2.success && res2.data) {
                  tokenStorage.setUser(res2.data);
                  set({
                    user: res2.data,
                    isAuthenticated: true,
                    accessToken: tokenStorage.getAccessToken(),
                    refreshToken: tokenStorage.getRefreshToken(),
                  });
                }
              } catch {
                get().clearSession();
              }
            }
          } else {
            get().clearSession();
          }
        } finally {
          set({ isLoading: false });
        }
      },

      // ── Clear all session data ────────────────────────────────────────
      clearSession() {
        tokenStorage.clearAll();
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },

      // ── Update user profile ───────────────────────────────────────────
      updateUser(user) {
        tokenStorage.setUser(user);
        set({ user });
      },

      setLoading: (loading) => set({ isLoading: loading }),
    }),
    { name: "AuthStore" },
  ),
);
