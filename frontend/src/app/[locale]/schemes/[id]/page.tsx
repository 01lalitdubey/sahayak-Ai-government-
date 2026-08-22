"use client";

import { use } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, ExternalLink, FileText, Mail, Phone, Eye, Calendar, MapPin, Building2, Landmark, AlertTriangle } from "lucide-react";
import { MainLayout } from "@/components/layout/MainLayout";
import { useSchemeByCode } from "@/hooks/use-schemes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { SchemeCategoryBadge, SchemeTypeBadge, FeaturedBadge, SchemeStatusBadge } from "@/components/schemes/SchemeStatusBadge";
import { formatDate } from "@/lib/utils";
import { useTranslations } from "next-intl";
import { TranslationFeedback } from "@/components/schemes/TranslationFeedback";

function DetailRow({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: React.ReactNode }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3 py-2 border-b last:border-0">
      <Icon className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <div className="text-sm font-medium break-words">{value}</div>
      </div>
    </div>
  );
}

export default function SchemeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const t = useTranslations("scheme_detail");
  const { id } = use(params);
  // id segment contains scheme_code (stable across re-imports)
  const { data, isLoading, isError } = useSchemeByCode(id);
  const scheme = data?.data;

  if (isError) return (
    <MainLayout>
      <div className="page-container py-16 text-center space-y-3">
        <AlertTriangle className="h-10 w-10 text-destructive mx-auto opacity-50" />
        <p className="font-medium">{t("not_found")}</p>
        <Button variant="outline" asChild><Link href="/schemes"><ArrowLeft className="h-4 w-4 mr-2" />{t("back")}</Link></Button>
      </div>
    </MainLayout>
  );

  return (
    <MainLayout>
      <div className="page-container py-8 max-w-4xl">
        <Button variant="ghost" size="sm" asChild className="mb-6 -ml-2">
          <Link href="/schemes"><ArrowLeft className="h-4 w-4 mr-1.5" />{t("all_schemes")}</Link>
        </Button>

        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-48 w-full rounded-xl" />
          </div>
        ) : scheme ? (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            {/* Header */}
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <SchemeTypeBadge type={scheme.scheme_type} />
                <SchemeCategoryBadge category={scheme.category} />
                <SchemeStatusBadge isActive={scheme.is_active} />
                {scheme.is_featured && <FeaturedBadge />}
              </div>
              <h1 className="text-2xl font-bold leading-tight">{scheme.name}</h1>
              <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
                <span className="font-mono">{scheme.scheme_code}</span>
                <span>·</span>
                <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5" />{t("views", { count: scheme.view_count })}</span>
              </div>
            </div>

            {/* Short description */}
            {scheme.short_description && (
              <p className="text-lg text-muted-foreground leading-relaxed">{scheme.short_description}</p>
            )}

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Main content */}
              <div className="lg:col-span-2 space-y-6">
                {scheme.full_description && (
                  <Card>
                    <CardHeader><CardTitle className="text-base">{t("overview")}</CardTitle></CardHeader>
                    <CardContent><p className="text-sm leading-relaxed whitespace-pre-line">{scheme.full_description}</p></CardContent>
                  </Card>
                )}
                {scheme.benefits && (
                  <Card>
                    <CardHeader><CardTitle className="text-base">{t("benefits")}</CardTitle></CardHeader>
                    <CardContent><p className="text-sm leading-relaxed whitespace-pre-line">{scheme.benefits}</p></CardContent>
                  </Card>
                )}
                <TranslationFeedback schemeId={scheme.id} />
              </div>

              {/* Sidebar */}
              <div className="space-y-4">
                <Card>
                  <CardHeader><CardTitle className="text-sm">{t("details")}</CardTitle></CardHeader>
                  <CardContent className="pt-0">
                    <DetailRow icon={Building2} label={t("ministry")} value={scheme.ministry} />
                    <DetailRow icon={Landmark} label={t("department")} value={scheme.department} />
                    <DetailRow icon={MapPin} label={t("state")} value={scheme.state ?? t("all_india")} />
                    <DetailRow icon={MapPin} label={t("district")} value={scheme.district} />
                    <DetailRow icon={Calendar} label={t("application_mode")} value={<span className="capitalize">{scheme.application_mode}</span>} />
                    {scheme.application_start_date && (
                      <DetailRow icon={Calendar} label={t("opens")} value={formatDate(scheme.application_start_date)} />
                    )}
                    {scheme.application_end_date && (
                      <DetailRow icon={Calendar} label={t("closes")} value={formatDate(scheme.application_end_date)} />
                    )}
                    <DetailRow icon={Calendar} label={t("added")} value={formatDate(scheme.created_at)} />
                  </CardContent>
                </Card>

                {(scheme.official_url || scheme.official_pdf_url || scheme.contact_email || scheme.contact_phone) && (
                  <Card>
                    <CardHeader><CardTitle className="text-sm">{t("links_contact")}</CardTitle></CardHeader>
                    <CardContent className="pt-0 space-y-2">
                      {scheme.official_url && (
                        <a href={scheme.official_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm text-primary hover:underline">
                          <ExternalLink className="h-3.5 w-3.5" />{t("official_website")}
                        </a>
                      )}
                      {scheme.official_pdf_url && (
                        <a href={scheme.official_pdf_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm text-primary hover:underline">
                          <FileText className="h-3.5 w-3.5" />{t("download_pdf")}
                        </a>
                      )}
                      {scheme.contact_email && (
                        <a href={`mailto:${scheme.contact_email}`} className="flex items-center gap-2 text-sm text-primary hover:underline">
                          <Mail className="h-3.5 w-3.5" />{scheme.contact_email}
                        </a>
                      )}
                      {scheme.contact_phone && (
                        <a href={`tel:${scheme.contact_phone}`} className="flex items-center gap-2 text-sm text-primary hover:underline">
                          <Phone className="h-3.5 w-3.5" />{scheme.contact_phone}
                        </a>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </motion.div>
        ) : null}
      </div>
    </MainLayout>
  );
}
