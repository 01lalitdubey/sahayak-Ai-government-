/**
 * useAuth — Sahayak AI
 * Single hook that components use to access auth state and actions.
 * Never import useAuthStore directly in components — use this hook.
 */

"use client";

import { useAuthStore } from "@/store/auth-store";
import type { UserRole } from "@/types/auth";

export function useAuth() {
  const {
    user,
    accessToken,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refresh,
    restoreSession,
    clearSession,
    updateUser,
  } = useAuthStore();

  const isAdmin = user?.role === "admin" || user?.role === "super_admin";
  const isSuperAdmin = user?.role === "super_admin";

  function hasRole(role: UserRole): boolean {
    return user?.role === role;
  }

  function hasAnyRole(...roles: UserRole[]): boolean {
    return roles.some((r) => user?.role === r);
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    isLoading,
    isAdmin,
    isSuperAdmin,
    hasRole,
    hasAnyRole,
    login,
    logout,
    refresh,
    restoreSession,
    clearSession,
    updateUser,
  };
}
