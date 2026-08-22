"use client";

import { useEffect, useState } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useCategories, useStates } from "@/hooks/use-schemes";
import { SORT_OPTIONS, PAGE_SIZE_OPTIONS } from "@/types/scheme";
import type { SchemeFilters, SortOption, SchemeCategory, SchemeType, ApplicationMode } from "@/types/scheme";
import { useTranslations } from "next-intl";

interface SchemeFiltersProps {
  filters: SchemeFilters;
  onChange: (f: Partial<SchemeFilters>) => void;
  onReset: () => void;
}

export function SchemeFiltersBar({ filters, onChange, onReset }: SchemeFiltersProps) {
  const t = useTranslations("schemes");
  const [localQuery, setLocalQuery] = useState(filters.query ?? "");
  const { data: categoriesData } = useCategories();
  const { data: statesData } = useStates();
  const [showFilters, setShowFilters] = useState(false);

  // Debounce search — eslint-disable-next-line used because onChange is stable from parent
  useEffect(() => {
    const t = setTimeout(() => {
      if (localQuery !== (filters.query ?? "")) {
        onChange({ query: localQuery || undefined, page: 1 });
      }
    }, 400);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localQuery]);

  const hasActiveFilters =
    filters.category || filters.scheme_type || filters.state ||
    filters.application_mode || filters.is_featured != null || filters.query;

  return (
    <div className="space-y-3">
      {/* Search + filter toggle */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("search_placeholder")}
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            className="pl-9"
            aria-label={t("search_placeholder")}
          />
          {localQuery && (
            <button
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              onClick={() => { setLocalQuery(""); onChange({ query: undefined, page: 1 }); }}
              aria-label={t("clear_search")}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Button
          variant={showFilters ? "default" : "outline"}
          size="icon"
          onClick={() => setShowFilters((v) => !v)}
          aria-label={t("toggle_filters")}
        >
          <SlidersHorizontal className="h-4 w-4" />
        </Button>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={onReset} className="text-muted-foreground">
            <X className="h-3.5 w-3.5 mr-1" /> {t("reset")}
          </Button>
        )}
      </div>

      {/* Expanded filter panel */}
      {showFilters && (
        <div className="rounded-lg border bg-card p-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Category */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("category")}</Label>
            <select
              className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              value={filters.category ?? ""}
              onChange={(e) => onChange({ category: (e.target.value as SchemeCategory) || undefined, page: 1 })}
              aria-label={t("category")}
            >
              <option value="">{t("all_categories")}</option>
              {categoriesData?.data.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          {/* State */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("state")}</Label>
            <select
              className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              value={filters.state ?? ""}
              onChange={(e) => onChange({ state: e.target.value || undefined, page: 1 })}
              aria-label={t("state")}
            >
              <option value="">{t("all_states")}</option>
              <option value="">{t("central_nationwide")}</option>
              {statesData?.data.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          {/* Scheme Type */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("scheme_type")}</Label>
            <select
              className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              value={filters.scheme_type ?? ""}
              onChange={(e) => onChange({ scheme_type: (e.target.value as SchemeType) || undefined, page: 1 })}
              aria-label={t("scheme_type")}
            >
              <option value="">{t("all_types")}</option>
              <option value="central">{t("central")}</option>
              <option value="state">{t("state")}</option>
            </select>
          </div>

          {/* Application Mode */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("application_mode")}</Label>
            <select
              className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              value={filters.application_mode ?? ""}
              onChange={(e) => onChange({ application_mode: (e.target.value as ApplicationMode) || undefined, page: 1 })}
              aria-label={t("application_mode")}
            >
              <option value="">{t("all_modes")}</option>
              <option value="online">{t("online")}</option>
              <option value="offline">{t("offline")}</option>
              <option value="both">{t("both")}</option>
            </select>
          </div>
        </div>
      )}

      {/* Sort + Page size row */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Label className="text-xs text-muted-foreground shrink-0">{t("sort_by")}</Label>
          <select
            className="h-8 rounded-md border border-input bg-transparent px-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
            value={filters.sort}
            onChange={(e) => onChange({ sort: e.target.value as SortOption, page: 1 })}
            aria-label={t("sort_by")}
          >
            {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{t(o.value as Parameters<typeof t>[0])}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <Label className="text-xs text-muted-foreground shrink-0">{t("per_page")}</Label>
          <select
            className="h-8 rounded-md border border-input bg-transparent px-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
            value={filters.page_size}
            onChange={(e) => onChange({ page_size: Number(e.target.value), page: 1 })}
            aria-label={t("per_page")}
          >
            {PAGE_SIZE_OPTIONS.map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
      </div>
    </div>
  );
}
