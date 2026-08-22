/**
 * Recommendations Layout — Sahayak AI (Phase 5)
 * Wraps the recommendations section with ProtectedRoute + MainLayout.
 * All child pages (/recommendations, /recommendations/[schemeId]) inherit this.
 */

import type { ReactNode } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { MainLayout } from "@/components/layout/MainLayout";
import { getTranslations } from "next-intl/server";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "metadata" });
  return {
    title: t("recommendations_title"),
    description: t("recommendations_desc"),
  };
}

interface RecommendationsLayoutProps {
  children: ReactNode;
}

export default function RecommendationsLayout({ children }: RecommendationsLayoutProps) {
  return (
    <ProtectedRoute>
      <MainLayout>{children}</MainLayout>
    </ProtectedRoute>
  );
}
