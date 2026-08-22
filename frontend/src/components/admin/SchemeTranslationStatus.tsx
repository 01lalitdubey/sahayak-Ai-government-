"use client";

import { CheckCircle2, Clock, AlertTriangle, XCircle, Globe } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useSchemeTranslationStatus } from "@/hooks/use-schemes";
import type { TranslationStatusValue } from "@/types/scheme";

interface Props {
  schemeId: string;
}

const STATUS_CONFIG: Record<
  TranslationStatusValue,
  { label: string; icon: React.ElementType; className: string; dotClass: string }
> = {
  published: {
    label: "Published",
    icon: CheckCircle2,
    className: "text-emerald-700 bg-emerald-50 ring-emerald-600/20",
    dotClass: "bg-emerald-500",
  },
  outdated: {
    label: "Outdated",
    icon: AlertTriangle,
    className: "text-amber-700 bg-amber-50 ring-amber-600/20",
    dotClass: "bg-amber-500",
  },
  processing: {
    label: "Processing",
    icon: Clock,
    className: "text-blue-700 bg-blue-50 ring-blue-600/20",
    dotClass: "bg-blue-500 animate-pulse",
  },
  missing: {
    label: "Missing",
    icon: XCircle,
    className: "text-gray-500 bg-gray-50 ring-gray-400/20",
    dotClass: "bg-gray-300",
  },
};

function TranslationStatusBadge({ status }: { status: TranslationStatusValue }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${cfg.className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${cfg.dotClass}`} />
      {cfg.label}
    </span>
  );
}

export function SchemeTranslationStatus({ schemeId }: Props) {
  const { data, isLoading, isError } = useSchemeTranslationStatus(schemeId);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 11 }).map((_, i) => (
          <Skeleton key={i} className="h-9 w-full rounded-md" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        Failed to load translation status.
      </div>
    );
  }

  const publishedCount = data.translations.filter((t) => t.status === "published").length;
  const total = data.translations.length;
  const coverage = total > 0 ? Math.round((publishedCount / total) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* Coverage bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Translation Coverage</span>
          <span className="text-sm font-semibold text-gray-900">{publishedCount}/{total} languages</span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-200">
          <div
            className="h-2 rounded-full bg-emerald-500 transition-all duration-500"
            style={{ width: `${coverage}%` }}
          />
        </div>
        <p className="mt-1 text-xs text-gray-500">{coverage}% published</p>
      </div>

      {/* English source row */}
      <div className="rounded-md border border-gray-100 bg-white divide-y divide-gray-50">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Globe className="h-4 w-4 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900">English</p>
              <p className="text-xs text-gray-400">Source language</p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium text-indigo-700 bg-indigo-50 ring-1 ring-inset ring-indigo-600/20">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
            Source
          </span>
        </div>

        {/* Language rows */}
        {data.translations.map((t) => (
          <div key={t.language_code} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors">
            <div>
              <p className="text-sm font-medium text-gray-900">{t.language_name}</p>
              <p className="text-xs text-gray-400 font-mono">{t.language_code.toUpperCase()}</p>
            </div>
            <div className="flex items-center gap-3">
              {t.version && (
                <span className="text-xs text-gray-400">v{t.version}</span>
              )}
              <TranslationStatusBadge status={t.status} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
