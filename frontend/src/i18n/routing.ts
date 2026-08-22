import { defineRouting } from "next-intl/routing";
import { createNavigation } from "next-intl/navigation";

export const locales = [
  "en",
  "hi",
  "ta",
  "te",
  "mr",
  "gu",
  "bn",
  "kn",
  "ml",
  "pa",
  "or",
  "as",
] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale = "en" as const;

export const routing = defineRouting({
  locales,
  defaultLocale,
  // Automatically redirect / to the user's locale (or defaultLocale)
  localePrefix: "as-needed",
});

// Lightweight wrappers around Next.js' navigation APIs
// that will consider the routing configuration
export const { Link, redirect, usePathname, useRouter } =
  createNavigation(routing);
