"use client";

import React, { useState, useCallback, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Plus,
  Search,
  X,
  ChevronLeft,
  ChevronRight,
  Archive,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SchemeTable } from "@/components/schemes/SchemeTable";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { MainLayout } from "@/components/layout/MainLayout";
import { showToast } from "@/components/ui/toast-utils";
import {
  useAdminSchemes,
  useArchiveScheme,
  useRestoreScheme,
  usePublishScheme,
} from "@/hooks/use-schemes";
import { useCategories } from "@/hooks/use-schemes";
import type { AdminSchemeFilters } from "@/types/scheme";

// ── Confirmation Dialog ────────────────────────────────────────────────────

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  confirmClass?: string;
  icon?: React.ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  confirmClass = "bg-red-600 hover:bg-red-700 text-white",
  icon,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onCancel} />
      <div className="relative z-10 w-full max-w-md rounded-2xl bg-white shadow-2xl border border-gray-100 p-6">
        <div className="flex items-start gap-4">
          {icon && <div className="flex-shrink-0 text-red-500 mt-0.5">{icon}</div>}
          <div>
            <h3 className="text-base font-semibold text-gray-900">{title}</h3>
            <p className="mt-2 text-sm text-gray-500">{description}</p>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="outline" onClick={onCancel}>Cancel</Button>
          <button
            onClick={onConfirm}
            className={`inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-semibold shadow-sm transition-colors ${confirmClass}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

function AdminSchemesContent() {
  const pathname = usePathname();
  const localePrefix = `/${pathname.split("/")[1]}`;

  // Filters state
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState<string | undefined>();
  const [category, setCategory] = useState<string | undefined>();
  const [schemeType, setSchemeType] = useState<string | undefined>();
  const [statusFilter, setStatusFilter] = useState<boolean | null | undefined>(undefined); // undefined = all
  const [page, setPage] = useState(1);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Mutations
  const archiveMut = useArchiveScheme();
  const restoreMut = useRestoreScheme();
  const publishMut = usePublishScheme();
  const { data: categoriesData } = useCategories();

  // Confirm dialog state
  const [confirm, setConfirm] = useState<{
    open: boolean;
    type: "archive" | "restore" | "publish" | "unpublish";
    id: string;
    name: string;
    isActive?: boolean;
  } | null>(null);

  // Filters object
  const filters: Partial<AdminSchemeFilters> = {
    query,
    category: category as AdminSchemeFilters["category"],
    scheme_type: schemeType as AdminSchemeFilters["scheme_type"],
    is_active: statusFilter,
    sort: "newest",
    page,
    page_size: 20,
  };

  const { data, isLoading } = useAdminSchemes(filters);
  const schemes = data?.data ?? [];
  const meta = data?.meta;

  // Debounced search
  const handleSearchChange = useCallback((val: string) => {
    setSearchInput(val);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setQuery(val.trim() || undefined);
      setPage(1);
    }, 300);
  }, []);

  const clearFilters = () => {
    setSearchInput("");
    setQuery(undefined);
    setCategory(undefined);
    setSchemeType(undefined);
    setStatusFilter(undefined);
    setPage(1);
  };

  const hasFilters = !!(query || category || schemeType || statusFilter !== undefined);

  // Action handlers
  const handleArchive = (id: string, name: string) => {
    setConfirm({ open: true, type: "archive", id, name });
  };

  const handleRestore = (id: string, name: string) => {
    setConfirm({ open: true, type: "restore", id, name });
  };

  const handlePublish = (id: string, isActive: boolean) => {
    setConfirm({ open: true, type: isActive ? "publish" : "unpublish", id, name: id, isActive });
  };

  const handleConfirm = async () => {
    if (!confirm) return;
    const { type, id, name } = confirm;
    setConfirm(null);

    try {
      if (type === "archive") {
        await archiveMut.mutateAsync(id);
        showToast(`"${name}" archived successfully.`, "success");
      } else if (type === "restore") {
        await restoreMut.mutateAsync(id);
        showToast(`"${name}" restored successfully.`, "success");
      } else if (type === "publish") {
        await publishMut.mutateAsync({ id, is_active: true });
        showToast("Scheme published.", "success");
      } else if (type === "unpublish") {
        await publishMut.mutateAsync({ id, is_active: false });
        showToast("Scheme unpublished.", "success");
      }
    } catch {
      showToast("Action failed. Please try again.", "error");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Scheme Management</h1>
            <p className="text-sm text-gray-500 mt-1">
              Manage government schemes, translations, and lifecycle.
              {meta && (
                <span className="ml-2 font-medium text-gray-700">{meta.total} total schemes</span>
              )}
            </p>
          </div>
          <Link
            href={`${localePrefix}/admin/schemes/create`}
            className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add New Scheme
          </Link>
        </div>

        {/* Filters bar */}
        <div className="rounded-xl border bg-white shadow-sm p-4">
          <div className="flex flex-wrap gap-3 items-end">
            {/* Search */}
            <div className="flex-1 min-w-[220px] max-w-sm">
              <Label htmlFor="search-schemes" className="text-xs font-medium text-gray-600 mb-1.5 block">
                Search
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                <Input
                  id="search-schemes"
                  value={searchInput}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  placeholder="Name, code, ministry…"
                  className="pl-9 h-9"
                />
              </div>
            </div>

            {/* Category */}
            <div className="min-w-[160px]">
              <Label className="text-xs font-medium text-gray-600 mb-1.5 block">Category</Label>
              <select
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                value={category ?? ""}
                onChange={(e) => { setCategory(e.target.value || undefined); setPage(1); }}
              >
                <option value="">All Categories</option>
                {categoriesData?.data.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Type */}
            <div className="min-w-[130px]">
              <Label className="text-xs font-medium text-gray-600 mb-1.5 block">Type</Label>
              <select
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                value={schemeType ?? ""}
                onChange={(e) => { setSchemeType(e.target.value || undefined); setPage(1); }}
              >
                <option value="">All Types</option>
                <option value="central">Central</option>
                <option value="state">State</option>
              </select>
            </div>

            {/* Status */}
            <div className="min-w-[140px]">
              <Label className="text-xs font-medium text-gray-600 mb-1.5 block">Status</Label>
              <select
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                value={statusFilter === undefined ? "all" : statusFilter === true ? "published" : "archived"}
                onChange={(e) => {
                  const v = e.target.value;
                  setStatusFilter(v === "all" ? undefined : v === "published" ? true : false);
                  setPage(1);
                }}
              >
                <option value="all">All Statuses</option>
                <option value="published">Published</option>
                <option value="archived">Draft / Archived</option>
              </select>
            </div>

            {/* Clear filters */}
            {hasFilters && (
              <div className="flex items-end">
                <Button variant="ghost" size="sm" onClick={clearFilters} className="h-9 gap-1 text-gray-500">
                  <X className="h-3.5 w-3.5" /> Clear
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Table */}
        <SchemeTable
          schemes={schemes}
          isLoading={isLoading}
          localePrefix={localePrefix}
          onArchive={handleArchive}
          onRestore={handleRestore}
          onPublish={handlePublish}
        />

        {/* Pagination */}
        {meta && meta.total_pages > 1 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Showing {(meta.page - 1) * meta.page_size + 1}–
              {Math.min(meta.page * meta.page_size, meta.total)} of {meta.total}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p - 1)}
                disabled={page <= 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-gray-700 tabular-nums">
                {meta.page} / {meta.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= meta.total_pages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        open={confirm?.open ?? false}
        title={
          confirm?.type === "archive"
            ? "Archive this scheme?"
            : confirm?.type === "restore"
            ? "Restore this scheme?"
            : confirm?.type === "publish"
            ? "Publish this scheme?"
            : "Unpublish this scheme?"
        }
        description={
          confirm?.type === "archive"
            ? `"${confirm?.name}" will be hidden from the public and all search results. It can be restored later. Audit history and translations will be preserved.`
            : confirm?.type === "restore"
            ? `"${confirm?.name}" will become publicly visible again. Any outdated translations will be re-queued automatically.`
            : confirm?.type === "publish"
            ? "This scheme will be published and visible to the public. Translation jobs will be queued automatically."
            : "This scheme will be hidden from public view."
        }
        confirmLabel={
          confirm?.type === "archive"
            ? "Archive"
            : confirm?.type === "restore"
            ? "Restore"
            : confirm?.type === "publish"
            ? "Publish"
            : "Unpublish"
        }
        confirmClass={
          confirm?.type === "archive"
            ? "bg-red-600 hover:bg-red-700 text-white"
            : confirm?.type === "restore"
            ? "bg-blue-600 hover:bg-blue-700 text-white"
            : confirm?.type === "publish"
            ? "bg-emerald-600 hover:bg-emerald-700 text-white"
            : "bg-amber-500 hover:bg-amber-600 text-white"
        }
        icon={
          confirm?.type === "archive" ? <Archive className="h-6 w-6" /> : <RotateCcw className="h-6 w-6 text-blue-500" />
        }
        onConfirm={handleConfirm}
        onCancel={() => setConfirm(null)}
      />
    </div>
  );
}

export default function AdminSchemesPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <MainLayout>
        <AdminSchemesContent />
      </MainLayout>
    </ProtectedRoute>
  );
}
