"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Eye, Calendar, MapPin, ArrowRight } from "lucide-react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SchemeCategoryBadge, SchemeTypeBadge, FeaturedBadge } from "./SchemeStatusBadge";
import { formatDate } from "@/lib/utils";
import type { SchemeSummary } from "@/types/scheme";

interface SchemeCardProps {
  scheme: SchemeSummary;
  index?: number;
}

export function SchemeCard({ scheme, index = 0 }: SchemeCardProps) {
  const t = useTranslations("schemes");
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.04 }}
    >
      <Link href={`/schemes/${scheme.scheme_code}`} className="block group h-full">
        <Card className="h-full transition-all duration-200 hover:shadow-md hover:border-primary/30 group-hover:-translate-y-0.5">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-mono text-muted-foreground mb-1">{scheme.scheme_code}</p>
                <h3 className="font-semibold text-sm leading-snug line-clamp-2 group-hover:text-primary transition-colors">
                  {scheme.name}
                </h3>
              </div>
              {scheme.is_featured && <FeaturedBadge />}
            </div>
            <div className="flex flex-wrap gap-1.5 mt-2">
              <SchemeTypeBadge type={scheme.scheme_type} />
              <SchemeCategoryBadge category={scheme.category} />
            </div>
          </CardHeader>
          <CardContent className="pt-0 space-y-3">
            {scheme.short_description && (
              <p className="text-xs text-muted-foreground line-clamp-2">{scheme.short_description}</p>
            )}
            <div className="space-y-1.5 text-xs text-muted-foreground">
              {scheme.ministry && (
                <div className="flex items-center gap-1.5 truncate">
                  <span className="shrink-0">🏛</span>
                  <span className="truncate">{scheme.ministry}</span>
                </div>
              )}
              {scheme.state && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-3 w-3 shrink-0" />
                  <span>{scheme.state}</span>
                </div>
              )}
              {scheme.application_end_date && (
                <div className="flex items-center gap-1.5">
                  <Calendar className="h-3 w-3 shrink-0" />
                  <span>{t("closes")} {formatDate(scheme.application_end_date)}</span>
                </div>
              )}
            </div>
            <div className="flex items-center justify-between pt-1 border-t">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Eye className="h-3 w-3" />
                {scheme.view_count.toLocaleString()}
              </div>
              <span className="text-xs font-medium text-primary flex items-center gap-1 group-hover:gap-2 transition-all">
                {t("view_details")} <ArrowRight className="h-3 w-3" />
              </span>
            </div>
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  );
}

export function SchemeCardSkeleton() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="h-3 w-24 bg-muted rounded animate-pulse mb-2" />
        <div className="h-4 w-full bg-muted rounded animate-pulse" />
        <div className="h-4 w-3/4 bg-muted rounded animate-pulse mt-1" />
        <div className="flex gap-1.5 mt-2">
          <div className="h-5 w-16 bg-muted rounded-full animate-pulse" />
          <div className="h-5 w-20 bg-muted rounded-full animate-pulse" />
        </div>
      </CardHeader>
      <CardContent className="pt-0 space-y-2">
        <div className="h-3 w-full bg-muted rounded animate-pulse" />
        <div className="h-3 w-2/3 bg-muted rounded animate-pulse" />
        <div className="h-3 w-1/2 bg-muted rounded animate-pulse" />
      </CardContent>
    </Card>
  );
}
