/**
 * RecommendationCard — Sahayak AI (Phase 5)
 * Full card for a recommended scheme shown in list/grid views.
 * Displays score, priority, reasons, eligibility, and action buttons.
 */

"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, MapPin, ExternalLink, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PriorityBadge } from "./PriorityBadge";
import { RecommendationScore } from "./RecommendationScore";
import { RecommendationReasonList } from "./RecommendationReasonList";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { RecommendationSummary } from "@/types/recommendation";
import { useTranslations } from "next-intl";

interface RecommendationCardProps {
  recommendation: RecommendationSummary;
  index?: number;
}

export function RecommendationCard({
  recommendation: rec,
  index = 0,
}: RecommendationCardProps) {
  const t = useTranslations("recommendations");
  const tSchemes = useTranslations("schemes");
  const detailHref = `${ROUTES.RECOMMENDATIONS}/${rec.scheme_id}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.04 }}
    >
      <Card
        className={cn(
          "h-full flex flex-col transition-all duration-200 hover:shadow-md hover:border-primary/30",
          rec.priority === "HIGH" && "border-emerald-500/20",
          rec.priority === "MEDIUM" && "border-amber-500/20"
        )}
      >
        <CardHeader className="pb-3">
          {/* Top row: score circle + scheme info */}
          <div className="flex items-start gap-4">
            <RecommendationScore score={rec.recommendation_score} size="sm" />
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-1.5 mb-1">
                <PriorityBadge priority={rec.priority} />
                {rec.is_featured && (
                  <Badge
                    variant="secondary"
                    className="text-[10px] px-1.5 py-0 bg-yellow-500/10 text-yellow-600 border-yellow-500/20"
                  >
                    ⭐ {tSchemes("featured")}
                  </Badge>
                )}
                {rec.eligibility_status === "eligible" && (
                  <Badge
                    variant="secondary"
                    className="text-[10px] px-1.5 py-0 bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                  >
                    ✓ {t("eligible_badge")}
                  </Badge>
                )}
              </div>
              <p className="text-[10px] font-mono text-muted-foreground mb-0.5">
                {rec.scheme_code}
              </p>
              <h3 className="font-semibold text-sm leading-snug line-clamp-2">
                {rec.scheme_name}
              </h3>
            </div>
          </div>

          {/* Meta */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground mt-2">
            {rec.ministry && (
              <span className="flex items-center gap-1 truncate">
                🏛 <span className="truncate">{rec.ministry}</span>
              </span>
            )}
            {rec.state && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" /> {rec.state}
              </span>
            )}
            {!rec.state && (
              <span className="flex items-center gap-1 text-blue-500">
                🌐 {t("all_states_badge")}
              </span>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-0 flex-1 flex flex-col gap-3">
          {/* Short description */}
          {rec.short_description && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              {rec.short_description}
            </p>
          )}

          {/* Top 2 reasons */}
          <RecommendationReasonList
            reasons={rec.reasons.slice(0, 2)}
            compact
          />

          {/* Missing info warning */}
          {rec.missing_information.length > 0 && (
            <div className="flex items-start gap-2 rounded-md bg-amber-500/5 border border-amber-500/20 px-2.5 py-2">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
              <p className="text-[11px] text-amber-700 dark:text-amber-400">
                {t("improve_score_msg")}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 mt-auto pt-2 border-t">
            <Button size="sm" variant="default" className="flex-1 h-8 text-xs" asChild>
              <Link href={detailHref}>
                {t("view_analysis")} <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            </Button>
            {rec.official_url && (
              <Button size="sm" variant="outline" className="h-8 text-xs px-2.5" asChild>
                <a href={rec.official_url} target="_blank" rel="noopener noreferrer">
                  {t("apply")} <ExternalLink className="h-3 w-3 ml-1" />
                </a>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Skeleton ──────────────────────────────────────────────────────────────

export function RecommendationCardSkeleton() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-4">
          <div className="h-14 w-14 rounded-full bg-muted animate-pulse shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="flex gap-1.5">
              <div className="h-4 w-12 bg-muted rounded-full animate-pulse" />
              <div className="h-4 w-16 bg-muted rounded-full animate-pulse" />
            </div>
            <div className="h-3 w-24 bg-muted rounded animate-pulse" />
            <div className="h-4 w-full bg-muted rounded animate-pulse" />
            <div className="h-4 w-3/4 bg-muted rounded animate-pulse" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0 space-y-3">
        <div className="h-3 w-full bg-muted rounded animate-pulse" />
        <div className="h-3 w-4/5 bg-muted rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-3 w-full bg-muted rounded animate-pulse" />
          <div className="h-3 w-3/4 bg-muted rounded animate-pulse" />
        </div>
        <div className="h-8 w-full bg-muted rounded animate-pulse mt-2" />
      </CardContent>
    </Card>
  );
}
