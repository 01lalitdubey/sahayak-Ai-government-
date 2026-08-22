"use client";

import Link from "next/link";
import { Edit, Trash2, RotateCcw, Eye, Globe, History, ExternalLink, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SchemeStatusBadge, SchemeCategoryBadge, SchemeTypeBadge } from "./SchemeStatusBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";
import type { SchemeSummary } from "@/types/scheme";

interface SchemeTableProps {
  schemes: SchemeSummary[];
  isLoading: boolean;
  localePrefix?: string;
  onArchive: (id: string, name: string) => void;
  onRestore: (id: string, name: string) => void;
  onPublish: (id: string, isActive: boolean) => void;
}

export function SchemeTable({
  schemes,
  isLoading,
  localePrefix = "/en",
  onArchive,
  onRestore,
  onPublish,
}: SchemeTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border bg-white overflow-hidden shadow-sm">
        <div className="p-4 space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (schemes.length === 0) {
    return (
      <div className="rounded-xl border bg-white p-16 text-center shadow-sm">
        <Globe className="mx-auto h-10 w-10 text-gray-300 mb-4" />
        <p className="font-medium text-gray-700">No schemes found</p>
        <p className="text-sm text-gray-400 mt-1">Try adjusting your filters or add a new scheme.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-white overflow-x-auto shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-gray-50/80 text-left">
            <th className="font-semibold text-gray-600 px-4 py-3.5 whitespace-nowrap">Name / Code</th>
            <th className="font-semibold text-gray-600 px-4 py-3.5 whitespace-nowrap hidden lg:table-cell">Category</th>
            <th className="font-semibold text-gray-600 px-4 py-3.5 whitespace-nowrap hidden md:table-cell">Ministry</th>
            <th className="font-semibold text-gray-600 px-4 py-3.5 whitespace-nowrap hidden xl:table-cell">State</th>
            <th className="font-semibold text-gray-600 px-4 py-3.5 whitespace-nowrap">Status</th>
            <th className="font-semibold text-gray-600 px-4 py-3.5 whitespace-nowrap hidden md:table-cell">Featured</th>
            <th className="font-semibold text-gray-600 px-4 py-3.5 whitespace-nowrap hidden xl:table-cell">Updated</th>
            <th className="font-semibold text-gray-600 px-4 py-3.5 text-right whitespace-nowrap">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {schemes.map((s) => (
            <tr key={s.id} className="hover:bg-gray-50/50 transition-colors">
              {/* Name / Code */}
              <td className="px-4 py-3.5">
                <div className="flex flex-col">
                  <Link
                    href={`${localePrefix}/admin/schemes/${s.id}`}
                    className="font-semibold text-gray-900 hover:text-primary-600 line-clamp-1 transition-colors"
                  >
                    {s.name}
                  </Link>
                  <span className="text-xs font-mono text-gray-400 mt-0.5">{s.scheme_code}</span>
                </div>
              </td>

              {/* Category */}
              <td className="px-4 py-3.5 hidden lg:table-cell">
                <div className="flex flex-wrap gap-1">
                  <SchemeTypeBadge type={s.scheme_type} />
                  <SchemeCategoryBadge category={s.category} />
                </div>
              </td>

              {/* Ministry */}
              <td className="px-4 py-3.5 hidden md:table-cell">
                <span className="text-gray-600 text-xs line-clamp-2 max-w-[160px]">
                  {s.ministry ?? "—"}
                </span>
              </td>

              {/* State */}
              <td className="px-4 py-3.5 hidden xl:table-cell">
                <span className="text-gray-500 text-xs">{s.state ?? "All India"}</span>
              </td>

              {/* Status */}
              <td className="px-4 py-3.5">
                <SchemeStatusBadge isActive={s.is_active} />
              </td>

              {/* Featured */}
              <td className="px-4 py-3.5 hidden md:table-cell">
                {s.is_featured ? (
                  <span className="inline-flex items-center gap-1 text-xs text-amber-600 font-medium">
                    <Star className="h-3 w-3 fill-current" /> Yes
                  </span>
                ) : (
                  <span className="text-gray-300 text-xs">—</span>
                )}
              </td>

              {/* Updated */}
              <td className="px-4 py-3.5 hidden xl:table-cell">
                <span className="text-xs text-gray-400">{formatDate(s.updated_at)}</span>
              </td>

              {/* Actions */}
              <td className="px-4 py-3.5">
                <div className="flex items-center justify-end gap-1">
                  {/* View detail */}
                  <Button variant="ghost" size="icon" className="h-8 w-8" asChild title="View Admin Detail">
                    <Link href={`${localePrefix}/admin/schemes/${s.id}`}>
                      <Eye className="h-4 w-4" />
                    </Link>
                  </Button>

                  {/* Edit */}
                  <Button variant="ghost" size="icon" className="h-8 w-8" asChild title="Edit Scheme">
                    <Link href={`${localePrefix}/admin/schemes/edit/${s.id}`}>
                      <Edit className="h-4 w-4" />
                    </Link>
                  </Button>

                  {/* Translation Status */}
                  <Button variant="ghost" size="icon" className="h-8 w-8 hidden sm:flex" asChild title="Translation Status">
                    <Link href={`${localePrefix}/admin/schemes/${s.id}#translations`}>
                      <Globe className="h-4 w-4 text-indigo-400" />
                    </Link>
                  </Button>

                  {/* Audit History */}
                  <Button variant="ghost" size="icon" className="h-8 w-8 hidden sm:flex" asChild title="Audit History">
                    <Link href={`${localePrefix}/admin/schemes/${s.id}#audit`}>
                      <History className="h-4 w-4 text-violet-400" />
                    </Link>
                  </Button>

                  {/* Preview public */}
                  <Button variant="ghost" size="icon" className="h-8 w-8 hidden lg:flex" asChild title="Public Preview">
                    <Link href={`${localePrefix}/schemes/${s.id}`} target="_blank">
                      <ExternalLink className="h-4 w-4 text-emerald-400" />
                    </Link>
                  </Button>

                  {/* Publish / Unpublish toggle */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className={`h-8 w-8 ${s.is_active ? "text-amber-500 hover:text-amber-700" : "text-emerald-500 hover:text-emerald-700"}`}
                    onClick={() => onPublish(s.id, !s.is_active)}
                    title={s.is_active ? "Unpublish" : "Publish"}
                  >
                    <span className="text-xs font-bold">{s.is_active ? "↓" : "↑"}</span>
                  </Button>

                  {/* Archive / Restore */}
                  {s.is_active ? (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 hover:text-red-600"
                      onClick={() => onArchive(s.id, s.name)}
                      title="Archive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  ) : (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 hover:text-blue-600"
                      onClick={() => onRestore(s.id, s.name)}
                      title="Restore"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
