"use client";

/**
 * Recommendations Page — Sahayak AI (Phase 5)
 * /recommendations
 *
 * Displays personalised scheme recommendations ranked by score.
 * Layout (ProtectedRoute + MainLayout) is handled by layout.tsx.
 */

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  RefreshCw,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  UserCircle,
  SearchX,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  RecommendationCard,
  RecommendationCardSkeleton,
  RecommendationFilters,
  RecommendationInsights,
  ProfileCompletionCard,
} from "@/components/recommendations";
import { useRecommendations, useRefreshRecommendations } from "@/hooks/use-recommendations";
import { ROUTES } from "@/lib/constants";
import type { RecommendationFilters as Filters } from "@/types/recommendation";
import { useTranslations } from "next-intl";

// ── Empty / Error states ───────────────────────────────────────────────────

function ProfileIncompleteState() {
  const t = useTranslations("recommendations");
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-24 text-center gap-5"
    >
      <div className="rounded-full bg-amber-500/10 p-6">
        <UserCircle className="h-14 w-14 text-amber-500" />
      </div>
      <div className="space-y-2 max-w-sm">
        <h2 className="text-xl font-bold">{t("complete_profile_title")}</h2>
        <p className="text-muted-foreground text-sm">
          {t("complete_profile_desc")}
        </p>
      </div>
      <Button asChild>
        <Link href={ROUTES.PROFILE}>
          {t("complete_profile")} <ArrowRight className="h-4 w-4 ml-1.5" />
        </Link>
      </Button>
    </motion.div>
  );
}

function NoResultsState({ onClear }: { onClear: () => void }) {
  const t = useTranslations("recommendations");
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-20 text-center gap-4"
    >
      <div className="rounded-full bg-muted p-5">
        <SearchX className="h-10 w-10 text-muted-foreground" />
      </div>
      <div className="space-y-1.5">
        <h3 className="font-semibold">{t("no_match_title")}</h3>
        <p className="text-sm text-muted-foreground">
          {t("no_match_desc")}
        </p>
      </div>
      <Button variant="outline" size="sm" onClick={onClear}>
        {t("clear_filters")}
      </Button>
    </motion.div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  const t = useTranslations("recommendations");
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-20 gap-4 text-center"
    >
      <div className="rounded-full bg-destructive/10 p-4">
        <AlertTriangle className="h-8 w-8 text-destructive" />
      </div>
      <div>
        <h3 className="font-semibold">{t("load_failed_title")}</h3>
        <p className="text-sm text-muted-foreground">
          {t("load_failed_desc")}
        </p>
      </div>
      <Button variant="outline" size="sm" onClick={onRetry}>
        {t("retry")}
      </Button>
    </motion.div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function RecommendationsPage() {
  const t = useTranslations("recommendations");
  const [filters, setFilters] = useState<Partial<Filters>>({
    sort: "score_desc",
    page: 1,
    page_size: 12,
  });

  const { data, isLoading, isError, error, refetch } = useRecommendations(filters);
  const refresh = useRefreshRecommendations();

  // Detect 422 (profile incomplete) from axios error response
  const isProfileIncomplete =
    isError &&
    (error as { response?: { status?: number } })?.response?.status === 422;

  function handleFilterChange(newFilters: Partial<Filters>) {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  }

  function handlePage(direction: "prev" | "next") {
    setFilters((prev) => ({
      ...prev,
      page:
        direction === "next"
          ? (prev.page ?? 1) + 1
          : Math.max(1, (prev.page ?? 1) - 1),
    }));
  }

  return (
    <div className="page-container py-8 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Sparkles className="h-7 w-7 text-primary" />
            {t("title")}
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            {t("subtitle")}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refresh.mutate()}
          disabled={refresh.isPending}
          aria-label="Refresh recommendations"
          id="btn-refresh-recommendations"
          className="shrink-0"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 mr-1.5 ${refresh.isPending ? "animate-spin" : ""}`}
          />
          {refresh.isPending ? t("refreshing") : t("refresh")}
        </Button>
      </motion.div>

      {/* Insights + Profile completion */}
      <div className="grid gap-4 sm:grid-cols-2">
        <RecommendationInsights />
        <ProfileCompletionCard />
      </div>

      {/* Profile incomplete — full state (no filter/grid) */}
      {isProfileIncomplete && <ProfileIncompleteState />}

      {/* Normal content */}
      {!isProfileIncomplete && (
        <>
          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <RecommendationFilters
                filters={filters}
                onChange={handleFilterChange}
                totalResults={data?.total}
                isLoading={isLoading}
              />
            </CardContent>
          </Card>

          {/* Grid */}
          <AnimatePresence mode="wait">
            {isError ? (
              <ErrorState key="error" onRetry={() => refetch()} />
            ) : isLoading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
              >
                {Array.from({ length: 6 }).map((_, i) => (
                  <RecommendationCardSkeleton key={i} />
                ))}
              </motion.div>
            ) : data?.data.length ? (
              <motion.div
                key="results"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {data.data.map((rec, i) => (
                    <RecommendationCard
                      key={rec.scheme_id}
                      recommendation={rec}
                      index={i}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {data.total_pages > 1 && (
                  <div className="flex items-center justify-center gap-3 pt-6">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={data.page <= 1}
                      onClick={() => handlePage("prev")}
                      aria-label={t("previous_page")}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      {t("page_of", { page: data.page, total: data.total_pages })}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={data.page >= data.total_pages}
                      onClick={() => handlePage("next")}
                      aria-label={t("next_page")}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </motion.div>
            ) : (
              <NoResultsState
                key="empty"
                onClear={() =>
                  handleFilterChange({
                    priority: undefined,
                    category: undefined,
                  })
                }
              />
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}
