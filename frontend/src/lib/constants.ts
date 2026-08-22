/**
 * Application-wide constants — Sahayak AI
 * Centralised here so magic strings never leak into components.
 */

export const APP_NAME = process.env["NEXT_PUBLIC_APP_NAME"] ?? "Sahayak AI";
export const APP_VERSION = process.env["NEXT_PUBLIC_APP_VERSION"] ?? "0.1.0";

export const API_BASE_URL =
  process.env["NEXT_PUBLIC_API_BASE_URL"] ?? "http://localhost:8000";

export const API_VERSION = process.env["NEXT_PUBLIC_API_VERSION"] ?? "v1";

export const API_URL = `${API_BASE_URL}/api/${API_VERSION}`;

/** Navigation routes used in Navbar and page redirects */
export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  CHAT: "/chat",
  SCHEMES: "/schemes",
  ELIGIBILITY: "/eligibility",
  PROFILE: "/profile",
  RECOMMENDATIONS: "/recommendations",
  ADMIN: "/admin",
  ADMIN_SCHEMES: "/admin/schemes",
  ADMIN_SCHEMES_CREATE: "/admin/schemes/create",
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];
