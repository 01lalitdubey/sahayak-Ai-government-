"use client";

/**
 * ProtectedRoute — Sahayak AI
 * Redirects unauthenticated users to /login.
 * Optionally enforces a required role.
 */

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { ROUTES } from "@/lib/constants";
import type { UserRole } from "@/types/auth";
import { LoadingScreen } from "./LoadingScreen";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: UserRole;
  fallback?: ReactNode;
}

export function ProtectedRoute({ children, requiredRole, fallback }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`${ROUTES.LOGIN}?redirect=${encodeURIComponent(window.location.pathname)}`);
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isLoading && isAuthenticated && requiredRole && user?.role !== requiredRole) {
      // Allow super_admin to access admin routes too
      const isAdminRole = user?.role === "admin" || user?.role === "super_admin";
      if (requiredRole === "admin" && isAdminRole) return;
      router.replace(ROUTES.DASHBOARD);
    }
  }, [isAuthenticated, isLoading, requiredRole, user, router]);

  if (isLoading) return <LoadingScreen />;
  if (!isAuthenticated) return null;
  if (requiredRole && user?.role !== requiredRole) {
    const isAdminRole = user?.role === "admin" || user?.role === "super_admin";
    if (requiredRole === "admin" && isAdminRole) return <>{children}</>;
    return fallback ?? null;
  }

  return <>{children}</>;
}
