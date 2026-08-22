"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PaginationMeta } from "@/types/scheme";
import { useTranslations } from "next-intl";

interface Props { meta: PaginationMeta; onPage: (p: number) => void; }

export function SchemePagination({ meta, onPage }: Props) {
  const t = useTranslations("schemes");
  if (meta.total_pages <= 1) return null;

  const pages: (number | "...")[] = [];
  const { page, total_pages } = meta;
  if (total_pages <= 7) {
    for (let i = 1; i <= total_pages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    for (let i = Math.max(2, page - 1); i <= Math.min(total_pages - 1, page + 1); i++) pages.push(i);
    if (page < total_pages - 2) pages.push("...");
    pages.push(total_pages);
  }

  return (
    <nav className="flex items-center justify-between pt-4" aria-label="Pagination">
      <p className="text-sm text-muted-foreground">
        {t("showing_results", {
          start: ((page - 1) * meta.page_size) + 1,
          end: Math.min(page * meta.page_size, meta.total),
          total: meta.total
        })}
      </p>
      <div className="flex items-center gap-1">
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => onPage(page - 1)} disabled={page <= 1} aria-label={t("previous_page")}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        {pages.map((p, i) =>
          p === "..." ? (
            <span key={`e${i}`} className="px-2 text-muted-foreground text-sm">…</span>
          ) : (
            <Button
              key={p}
              variant={p === page ? "default" : "outline"}
              size="icon"
              className="h-8 w-8 text-xs"
              onClick={() => onPage(p as number)}
              aria-label={t("page_number", { p })}
              aria-current={p === page ? "page" : undefined}
            >
              {p}
            </Button>
          )
        )}
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => onPage(page + 1)} disabled={page >= total_pages} aria-label={t("next_page")}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </nav>
  );
}
