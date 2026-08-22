/**
 * RecommendationGrid — Sahayak AI (Phase 5)
 * Responsive grid layout wrapper for recommendation cards.
 * Handles loading skeletons and empty state.
 */

import { cn } from "@/lib/utils";
import { RecommendationCard, RecommendationCardSkeleton } from "./RecommendationCard";
import type { RecommendationSummary } from "@/types/recommendation";

interface RecommendationGridProps {
  recommendations: RecommendationSummary[];
  isLoading?: boolean;
  skeletonCount?: number;
  className?: string;
}

export function RecommendationGrid({
  recommendations,
  isLoading = false,
  skeletonCount = 6,
  className,
}: RecommendationGridProps) {
  return (
    <div
      className={cn(
        "grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
        className
      )}
    >
      {isLoading
        ? Array.from({ length: skeletonCount }).map((_, i) => (
            <RecommendationCardSkeleton key={i} />
          ))
        : recommendations.map((rec, i) => (
            <RecommendationCard
              key={rec.scheme_id}
              recommendation={rec}
              index={i}
            />
          ))}
    </div>
  );
}
