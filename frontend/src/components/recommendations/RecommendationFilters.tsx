/**
 * RecommendationFilters — Sahayak AI (Phase 5)
 * Filter bar for the recommendations page: priority, sort.
 * Uses native <select> elements — no shadcn/ui Select dependency.
 */

"use client";

import { Filter, ArrowUpDown, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RecommendationFilters as Filters } from "@/types/recommendation";
import { useTranslations } from "next-intl";

interface RecommendationFiltersProps {
  filters: Partial<Filters>;
  onChange: (filters: Partial<Filters>) => void;
  totalResults?: number;
  isLoading?: boolean;
}

const selectCls =
  "h-8 rounded-md border border-input bg-background px-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring appearance-none cursor-pointer";

export function RecommendationFilters({
  filters,
  onChange,
  totalResults,
  isLoading,
}: RecommendationFiltersProps) {
  const t = useTranslations("recommendations");
  const hasActiveFilters = !!(filters.priority);

  const PRIORITY_OPTIONS = [
    { value: "", label: t("all_priorities") },
    { value: "HIGH", label: "🟢 " + t("priority_high") },
    { value: "MEDIUM", label: "🟡 " + t("priority_medium") },
    { value: "LOW", label: "⚪ " + t("priority_low") },
  ];

  const SORT_OPTIONS = [
    { value: "score_desc", label: t("highest_score") },
    { value: "score_asc", label: t("lowest_score") },
    { value: "priority", label: t("priority") },
    { value: "alphabetical", label: t("a_z") },
  ];

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Filter className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">{t("filter_label")}</span>
      </div>

      {/* Priority filter */}
      <select
        id="filter-priority"
        aria-label="Filter by priority"
        value={filters.priority ?? ""}
        onChange={(e) =>
          onChange({
            ...filters,
            priority: (e.target.value as Filters["priority"]) || undefined,
            page: 1,
          })
        }
        className={cn(selectCls, "w-36")}
      >
        {PRIORITY_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {/* Sort */}
      <div className="flex items-center gap-1.5 ml-auto">
        <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
        <select
          id="filter-sort"
          aria-label="Sort results"
          value={filters.sort ?? "score_desc"}
          onChange={(e) =>
            onChange({ ...filters, sort: e.target.value as Filters["sort"], page: 1 })
          }
          className={cn(selectCls, "w-36")}
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Clear active filters */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 px-2 text-xs text-muted-foreground"
          onClick={() => onChange({ sort: filters.sort, page: 1 })}
        >
          <X className="h-3 w-3 mr-1" /> {t("clear")}
        </Button>
      )}

      {/* Results count */}
      {!isLoading && totalResults !== undefined && (
        <Badge variant="secondary" className="ml-1 text-xs">
          {t("results_count", { count: totalResults })}
        </Badge>
      )}
    </div>
  );
}
