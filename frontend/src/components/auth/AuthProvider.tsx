"use client";

/**
 * AuthProvider — Sahayak AI
 * Restores session on mount. Wraps the whole app inside Providers.
 * Shows LoadingScreen while session is being verified.
 */

import { useEffect, type ReactNode } from "react";
import { useAuthStore } from "@/store/auth-store";
import { LoadingScreen } from "./LoadingScreen";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { restoreSession, isLoading } = useAuthStore();

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  if (isLoading) {
    return <LoadingScreen />;
  }

  return <>{children}</>;
}
