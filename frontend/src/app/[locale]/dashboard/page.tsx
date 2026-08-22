"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Search,
  CheckCircle2,
  Star,
  Sparkles,
  Settings,
  Globe,
} from "lucide-react";
import { MainLayout } from "@/components/layout/MainLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SchemeCard, SchemeCardSkeleton } from "@/components/schemes/SchemeCard";
import {
  RecommendationCard,
  RecommendationCardSkeleton,
  ProfileCompletionCard,
  RecommendationInsights,
} from "@/components/recommendations";
import { useFeaturedSchemes, useRecentSchemes } from "@/hooks/use-schemes";
import { useTopRecommendations } from "@/hooks/use-recommendations";
import { useAuth } from "@/hooks/use-auth";
import { ROUTES } from "@/lib/constants";

function DashboardContent() {
  const { user, isAdmin } = useAuth();
  const t = useTranslations("dashboard");
  const { data: featured, isLoading: loadingFeatured } = useFeaturedSchemes(3);
  const { data: recent, isLoading: loadingRecent } = useRecentSchemes(3);
  const { data: topRecs, isLoading: loadingTopRecs } = useTopRecommendations(3);

  const quickLinks = [
    {
      href: ROUTES.RECOMMENDATIONS,
      icon: Sparkles,
      label: t("my_recommendations"),
      desc: t("my_recs_desc"),
    },
    {
      href: ROUTES.SCHEMES,
      icon: Search,
      label: t("browse_schemes"),
      desc: t("browse_desc"),
    },
    {
      href: ROUTES.ELIGIBILITY,
      icon: CheckCircle2,
      label: t("check_eligibility"),
      desc: t("check_desc"),
    },
    ...(isAdmin
      ? [
          {
            href: "/admin/schemes",
            icon: Settings,
            label: "Manage Schemes",
            desc: "Add, edit, or remove schemes.",
          },
          {
            href: "/admin/tms",
            icon: Globe,
            label: "Translation TMS",
            desc: "Manage machine translations.",
          },
        ]
      : []),
  ];

  const hasTopRecs = (topRecs?.data?.length ?? 0) > 0;

  return (
    <div className="page-container py-8 space-y-8">
      {/* Welcome */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold">
          {t("welcome")}, {user?.full_name?.split(" ")[0] ?? "there"} 👋
        </h1>
        <p className="text-muted-foreground mt-1">
          {t("subtitle")}
        </p>
      </motion.div>

      {/* Profile completion + Insights (side by side on md+) */}
      <div className="grid gap-4 md:grid-cols-2">
        <ProfileCompletionCard />
        <RecommendationInsights />
      </div>

      {/* Quick links */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {quickLinks.map(({ href, icon: Icon, label, desc }, i) => (
          <motion.div
            key={href}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <Link href={href} className="block group">
              <Card className="h-full hover:shadow-md hover:border-primary/30 transition-all group-hover:-translate-y-0.5 duration-200">
                <CardContent className="p-5 flex items-start gap-4">
                  <div className="rounded-lg bg-primary/10 p-2.5">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm">{label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all mt-0.5" />
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Top Recommendations */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" /> {t("top_recommendations")}
          </h2>
          <Button variant="ghost" size="sm" asChild>
            <Link href={ROUTES.RECOMMENDATIONS}>
              {t("view_all")} <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </Link>
          </Button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loadingTopRecs ? (
            Array.from({ length: 3 }).map((_, i) => (
              <RecommendationCardSkeleton key={i} />
            ))
          ) : hasTopRecs ? (
            topRecs!.data.map((rec, i) => (
              <RecommendationCard key={rec.scheme_id} recommendation={rec} index={i} />
            ))
          ) : (
            <p className="text-sm text-muted-foreground col-span-full">
              {t("complete_profile_prompt")}{" "}
              <Link href={ROUTES.PROFILE} className="text-primary hover:underline">
                {t("update_profile")} →
              </Link>
            </p>
          )}
        </div>
      </section>

      {/* Featured schemes */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg flex items-center gap-2">
            <Star className="h-4 w-4 text-yellow-500 fill-current" /> {t("featured_schemes")}
          </h2>
          <Button variant="ghost" size="sm" asChild>
            <Link href={ROUTES.SCHEMES}>
              {t("view_all")} <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </Link>
          </Button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loadingFeatured
            ? Array.from({ length: 3 }).map((_, i) => <SchemeCardSkeleton key={i} />)
            : featured?.data.length
              ? featured.data.map((s, i) => <SchemeCard key={s.id} scheme={s} index={i} />)
              : <p className="text-sm text-muted-foreground col-span-full">{t("no_featured")}</p>}
        </div>
      </section>

      {/* Recent schemes */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg">{t("recently_added")}</h2>
          <Button variant="ghost" size="sm" asChild>
            <Link href={`${ROUTES.SCHEMES}?sort=newest`}>
              {t("view_all")} <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </Link>
          </Button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loadingRecent
            ? Array.from({ length: 3 }).map((_, i) => <SchemeCardSkeleton key={i} />)
            : recent?.data.length
              ? recent.data.map((s, i) => <SchemeCard key={s.id} scheme={s} index={i} />)
              : <p className="text-sm text-muted-foreground col-span-full">{t("no_recent")}</p>}
        </div>
      </section>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <MainLayout>
        <DashboardContent />
      </MainLayout>
    </ProtectedRoute>
  );
}
