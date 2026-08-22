/**
 * ProfileCompletionCard — Sahayak AI (Phase 5)
 * Dashboard card showing profile completion percentage, missing fields,
 * and a CTA to complete the profile.
 */

"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { UserCheck, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useProfileCompletion } from "@/hooks/use-recommendations";
import { useTranslations } from "next-intl";

export function ProfileCompletionCard() {
  const t = useTranslations("recommendations");
  const { data, isLoading } = useProfileCompletion();

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="h-4 w-40 bg-muted rounded animate-pulse" />
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="h-2 w-full bg-muted rounded animate-pulse" />
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-3 w-3/4 bg-muted rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const pct = data.completion_percentage;
  const isComplete = pct === 100;

  const progressColor =
    pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-rose-500";

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Card className={cn(isComplete && "border-emerald-500/30")}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "rounded-lg p-2",
                  isComplete ? "bg-emerald-500/10" : "bg-amber-500/10"
                )}
              >
                <UserCheck
                  className={cn(
                    "h-4 w-4",
                    isComplete ? "text-emerald-500" : "text-amber-500"
                  )}
                />
              </div>
              <div>
                <p className="font-semibold text-sm">{t("profile_completion")}</p>
                <p className="text-xs text-muted-foreground">
                  {t("fields_filled", { filled: data.filled_count, total: data.total_fields })}
                </p>
              </div>
            </div>
            <span
              className={cn(
                "text-2xl font-bold",
                pct >= 80 ? "text-emerald-500" : pct >= 50 ? "text-amber-500" : "text-rose-500"
              )}
            >
              {pct.toFixed(0)}%
            </span>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Progress bar */}
          <div className="space-y-1.5">
            <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
              <motion.div
                className={cn("h-full rounded-full", progressColor)}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>

          {/* Missing fields */}
          {data.missing_fields.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">{t("missing")}</p>
              <div className="flex flex-wrap gap-1.5">
                {data.missing_fields.slice(0, 5).map((field) => (
                  <span
                    key={field}
                    className="inline-flex items-center gap-1 text-[11px] rounded-full px-2 py-0.5 bg-muted text-muted-foreground"
                  >
                    <AlertCircle className="h-2.5 w-2.5" />
                    {field}
                  </span>
                ))}
                {data.missing_fields.length > 5 && (
                  <span className="text-[11px] text-muted-foreground">
                    {t("more", { count: data.missing_fields.length - 5 })}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Filled fields summary (if complete) */}
          {isComplete && (
            <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
              {t("profile_complete_msg")}
            </div>
          )}

          {/* CTA */}
          {!isComplete && (
            <Button size="sm" variant="outline" className="w-full h-8 text-xs" asChild>
              <Link href={ROUTES.PROFILE}>
                {t("complete_profile")} <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            </Button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
