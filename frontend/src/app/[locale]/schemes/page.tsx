"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { MainLayout } from "@/components/layout/MainLayout";
import { SchemeCard, SchemeCardSkeleton } from "@/components/schemes/SchemeCard";
import { SchemeFiltersBar } from "@/components/schemes/SchemeFilters";
import { SchemePagination } from "@/components/schemes/SchemePagination";
import { useSchemes } from "@/hooks/use-schemes";
import { AlertTriangle, SearchX } from "lucide-react";
import type { SchemeFilters } from "@/types/scheme";

const DEFAULT_FILTERS: SchemeFilters = {
  sort: "newest",
  page: 1,
  page_size: 20,
};

export default function SchemesPage() {
  const t = useTranslations("schemes");
  const [filters, setFilters] = useState<SchemeFilters>(DEFAULT_FILTERS);
  const { data, isLoading, isError } = useSchemes(filters);

  function updateFilters(partial: Partial<SchemeFilters>) {
    setFilters((prev) => ({ ...prev, ...partial }));
  }

  return (
    <MainLayout>
      <div className="page-container py-8 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-muted-foreground mt-1">
            {t("subtitle")}
          </p>
        </div>

        {/* Filters */}
        <SchemeFiltersBar
          filters={filters}
          onChange={updateFilters}
          onReset={() => setFilters(DEFAULT_FILTERS)}
        />

        {/* Results count */}
        {data && (
          <p className="text-sm text-muted-foreground">
            {data.meta.total} {data.meta.total !== 1 ? "schemes" : "scheme"} found
          </p>
        )}

        {/* Error */}
        {isError && (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <AlertTriangle className="h-10 w-10 text-destructive opacity-50" />
            <p className="text-muted-foreground">{t("no_results")}</p>
          </div>
        )}

        {/* Loading skeletons */}
        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => <SchemeCardSkeleton key={i} />)}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && data?.data.length === 0 && (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <SearchX className="h-10 w-10 text-muted-foreground opacity-50" />
            <p className="font-medium">{t("no_results")}</p>
            <p className="text-sm text-muted-foreground">{t("no_results_desc")}</p>
          </div>
        )}

        {/* Scheme grid */}
        {!isLoading && !isError && data && data.data.length > 0 && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {data.data.map((scheme, i) => (
                <SchemeCard key={scheme.id} scheme={scheme} index={i} />
              ))}
            </div>
            <SchemePagination meta={data.meta} onPage={(p) => updateFilters({ page: p })} />
          </>
        )}
      </div>
    </MainLayout>
  );
}
