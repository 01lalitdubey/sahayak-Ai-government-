/**
 * RecommendationInsights — Sahayak AI (Phase 5)
 * Dashboard summary card: total recs, HIGH count, profile completion %.
 */

"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { TrendingUp, ArrowRight, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";
import { useTopRecommendations, useProfileCompletion } from "@/hooks/use-recommendations";
import { cn } from "@/lib/utils";
import { useTranslations } from "next-intl";

export function RecommendationInsights() {
  const t = useTranslations("recommendations");
  const { data: top, isLoading: loadingTop } = useTopRecommendations(20);
  const { data: profile, isLoading: loadingProfile } = useProfileCompletion();

  const loading = loadingTop || loadingProfile;

  if (loading) {
    return (
      <Card>
        <CardContent className="p-5">
          <div className="grid grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="space-y-1.5">
                <div className="h-7 w-16 bg-muted rounded animate-pulse" />
                <div className="h-3 w-24 bg-muted rounded animate-pulse" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const allRecs = top?.data ?? [];
  const highCount = allRecs.filter((r) => r.priority === "HIGH").length;
  const profilePct = profile?.completion_percentage ?? 0;

  const stats = [
    {
      value: allRecs.length,
      label: t("stat_recs"),
      color: "text-primary",
      suffix: allRecs.length === 0 ? "" : "+",
    },
    {
      value: highCount,
      label: t("stat_high"),
      color: "text-emerald-500",
      suffix: "",
    },
    {
      value: `${profilePct.toFixed(0)}%`,
      label: t("stat_profile"),
      color:
        profilePct >= 80
          ? "text-emerald-500"
          : profilePct >= 50
          ? "text-amber-500"
          : "text-rose-500",
      suffix: "",
    },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="border-primary/10">
        <CardContent className="p-5">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="rounded-lg bg-primary/10 p-1.5">
                <Sparkles className="h-4 w-4 text-primary" />
              </div>
              <p className="font-semibold text-sm">{t("insights_title")}</p>
            </div>
            <Button variant="ghost" size="sm" className="h-7 text-xs" asChild>
              <Link href={ROUTES.RECOMMENDATIONS}>
                {t("view_all")} <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            </Button>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {stats.map(({ value, label, color, suffix }) => (
              <div key={label}>
                <p className={cn("text-2xl font-bold", color)}>
                  {value}{suffix}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {allRecs.length === 0 && (
            <p className="text-xs text-muted-foreground mt-3 flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5" />
              {t("unlock_prompt")}
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
