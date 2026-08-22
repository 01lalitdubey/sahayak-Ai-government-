"use client";

import React, { use } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ArrowLeft,
  Edit,
  Archive,
  RotateCcw,
  ExternalLink,
  Globe,
  Star,
  Building,
  MapPin,
  Calendar,
  Phone,
  Mail,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { MainLayout } from "@/components/layout/MainLayout";
import { SchemeStatusBadge, SchemeTypeBadge, SchemeCategoryBadge } from "@/components/schemes/SchemeStatusBadge";
import { SchemeTranslationStatus } from "@/components/admin/SchemeTranslationStatus";
import { SchemeAuditHistory } from "@/components/admin/SchemeAuditHistory";
import { showToast } from "@/components/ui/toast-utils";
import {
  useAdminScheme,
  useArchiveScheme,
  useRestoreScheme,
  usePublishScheme,
} from "@/hooks/use-schemes";
import { formatDate } from "@/lib/utils";
import { useRouter } from "next/navigation";

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value) return null;
  return (
    <div className="py-3 grid grid-cols-3 gap-4 border-b border-gray-50 last:border-0">
      <dt className="text-sm font-medium text-gray-500">{label}</dt>
      <dd className="text-sm text-gray-900 col-span-2">{value}</dd>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-6 py-4 border-b bg-gray-50/80">
        {icon && <span className="text-gray-400">{icon}</span>}
        <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">{title}</h2>
      </div>
      <div className="px-6 py-2">{children}</div>
    </div>
  );
}

function AdminSchemeDetailContent({ id }: { id: string }) {
  const pathname = usePathname();
  const localePrefix = `/${pathname.split("/")[1]}`;
  const router = useRouter();

  const { data, isLoading, isError } = useAdminScheme(id);
  const archiveMut = useArchiveScheme();
  const restoreMut = useRestoreScheme();
  const publishMut = usePublishScheme();

  const scheme = data?.data;

  const handleArchive = async () => {
    if (!scheme) return;
    if (!confirm(`Archive "${scheme.name}"? It will disappear from public view.`)) return;
    try {
      await archiveMut.mutateAsync(id);
      showToast("Scheme archived.", "success");
    } catch {
      showToast("Failed to archive scheme.", "error");
    }
  };

  const handleRestore = async () => {
    if (!scheme) return;
    try {
      await restoreMut.mutateAsync(id);
      showToast("Scheme restored and publicly visible.", "success");
    } catch {
      showToast("Failed to restore scheme.", "error");
    }
  };

  const handleTogglePublish = async () => {
    if (!scheme) return;
    const newState = !scheme.is_active;
    try {
      await publishMut.mutateAsync({ id, is_active: newState });
      showToast(newState ? "Scheme published." : "Scheme unpublished.", "success");
    } catch {
      showToast("Failed to change publish status.", "error");
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (isError || !scheme) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8 text-center">
        <p className="text-red-600 font-medium">Scheme not found or insufficient permissions.</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>Go Back</Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Back + Title */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <Button variant="ghost" size="sm" asChild className="-ml-2 mb-2">
              <Link href={`${localePrefix}/admin/schemes`}>
                <ArrowLeft className="h-4 w-4 mr-1.5" /> Back to Schemes
              </Link>
            </Button>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">{scheme.name}</h1>
              <SchemeStatusBadge isActive={scheme.is_active} />
              {scheme.is_featured && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-200">
                  <Star className="h-3 w-3 fill-current" /> Featured
                </span>
              )}
            </div>
            <p className="mt-1 text-sm font-mono text-gray-400">{scheme.scheme_code}</p>
          </div>

          {/* Action bar */}
          <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
            <Button variant="outline" size="sm" asChild>
              <Link href={`${localePrefix}/admin/schemes/edit/${id}`}>
                <Edit className="h-4 w-4 mr-1.5" /> Edit
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleTogglePublish}
              disabled={publishMut.isPending}
              className={scheme.is_active ? "text-amber-600 border-amber-200 hover:bg-amber-50" : "text-emerald-600 border-emerald-200 hover:bg-emerald-50"}
            >
              {scheme.is_active ? "Unpublish" : "Publish"}
            </Button>
            {scheme.is_active ? (
              <Button variant="outline" size="sm" onClick={handleArchive} disabled={archiveMut.isPending} className="text-red-600 border-red-200 hover:bg-red-50">
                <Archive className="h-4 w-4 mr-1.5" /> Archive
              </Button>
            ) : (
              <Button variant="outline" size="sm" onClick={handleRestore} disabled={restoreMut.isPending} className="text-blue-600 border-blue-200 hover:bg-blue-50">
                <RotateCcw className="h-4 w-4 mr-1.5" /> Restore
              </Button>
            )}
            {scheme.official_url && (
              <Button variant="outline" size="sm" asChild>
                <a href={scheme.official_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-1.5" /> Official Site
                </a>
              </Button>
            )}
          </div>
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: scheme details */}
          <div className="lg:col-span-2 space-y-6">

            {/* Overview */}
            <Section title="Overview" icon={<FileText className="h-4 w-4" />}>
              <dl>
                <DetailRow label="Short Description" value={scheme.short_description} />
                <DetailRow label="Full Description" value={
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{scheme.full_description}</p>
                } />
                <DetailRow label="Benefits" value={
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{scheme.benefits}</p>
                } />
              </dl>
            </Section>

            {/* Classification */}
            <Section title="Classification" icon={<Building className="h-4 w-4" />}>
              <dl>
                <DetailRow label="Type" value={<SchemeTypeBadge type={scheme.scheme_type} />} />
                <DetailRow label="Category" value={<SchemeCategoryBadge category={scheme.category} />} />
                <DetailRow label="Ministry" value={scheme.ministry} />
                <DetailRow label="Department" value={scheme.department} />
                <DetailRow label="State" value={scheme.state ?? "All India (Central)"} />
                <DetailRow label="District" value={scheme.district} />
              </dl>
            </Section>

            {/* Application */}
            <Section title="Application Details" icon={<Calendar className="h-4 w-4" />}>
              <dl>
                <DetailRow label="Mode" value={<span className="capitalize">{scheme.application_mode}</span>} />
                <DetailRow label="Start Date" value={scheme.application_start_date ? formatDate(scheme.application_start_date) : null} />
                <DetailRow label="End Date" value={scheme.application_end_date ? formatDate(scheme.application_end_date) : null} />
                <DetailRow label="Process" value={
                  scheme.application_process ? (
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{scheme.application_process}</p>
                  ) : null
                } />
                <DetailRow label="Required Documents" value={
                  scheme.required_documents ? (
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{scheme.required_documents}</p>
                  ) : null
                } />
              </dl>
            </Section>

            {/* Contact & URLs */}
            <Section title="Contact & Links" icon={<Phone className="h-4 w-4" />}>
              <dl>
                <DetailRow label="Official URL" value={
                  scheme.official_url ? (
                    <a href={scheme.official_url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline flex items-center gap-1">
                      {scheme.official_url} <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : null
                } />
                <DetailRow label="PDF URL" value={scheme.official_pdf_url} />
                <DetailRow label="Contact Email" value={
                  scheme.contact_email ? (
                    <a href={`mailto:${scheme.contact_email}`} className="text-primary-600 hover:underline flex items-center gap-1">
                      <Mail className="h-3 w-3" /> {scheme.contact_email}
                    </a>
                  ) : null
                } />
                <DetailRow label="Contact Phone" value={
                  scheme.contact_phone ? (
                    <a href={`tel:${scheme.contact_phone}`} className="flex items-center gap-1">
                      <Phone className="h-3 w-3" /> {scheme.contact_phone}
                    </a>
                  ) : null
                } />
              </dl>
            </Section>

            {/* Metadata */}
            <Section title="Metadata" icon={<MapPin className="h-4 w-4" />}>
              <dl>
                <DetailRow label="Created" value={formatDate(scheme.created_at)} />
                <DetailRow label="Last Updated" value={formatDate(scheme.updated_at)} />
                <DetailRow label="Views" value={scheme.view_count.toLocaleString()} />
              </dl>
            </Section>

          </div>

          {/* Right: translation status + audit history */}
          <div className="space-y-6">

            {/* Translation Status */}
            <div id="translations" className="rounded-xl border bg-white shadow-sm overflow-hidden">
              <div className="flex items-center gap-2 px-6 py-4 border-b bg-gray-50/80">
                <Globe className="h-4 w-4 text-gray-400" />
                <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Translations</h2>
              </div>
              <div className="px-6 py-4">
                <SchemeTranslationStatus schemeId={id} />
              </div>
            </div>

            {/* Audit History */}
            <div id="audit" className="rounded-xl border bg-white shadow-sm overflow-hidden">
              <div className="flex items-center gap-2 px-6 py-4 border-b bg-gray-50/80">
                <FileText className="h-4 w-4 text-gray-400" />
                <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Audit History</h2>
              </div>
              <div className="px-6 py-4">
                <SchemeAuditHistory schemeId={id} />
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminSchemeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <ProtectedRoute requiredRole="admin">
      <MainLayout>
        <AdminSchemeDetailContent id={id} />
      </MainLayout>
    </ProtectedRoute>
  );
}
