"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { CheckCircle2, XCircle, AlertCircle, User, ArrowRight } from "lucide-react";
import { MainLayout } from "@/components/layout/MainLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyEligibility } from "@/hooks/use-eligibility";
import { cn } from "@/lib/utils";
import type { EligibilitySummary, EligibilityStatus } from "@/types/eligibility";

const STATUS_CONFIG: Record<EligibilityStatus, { label: string; icon: React.ElementType; colour: string }> = {
  eligible: { label: "Eligible", icon: CheckCircle2, colour: "text-green-600" },
  not_eligible: { label: "Not Eligible", icon: XCircle, colour: "text-red-600" },
  incomplete_profile: { label: "Incomplete Profile", icon: AlertCircle, colour: "text-yellow-600" },
  no_rules: { label: "No Rules", icon: AlertCircle, colour: "text-muted-foreground" },
};

function SchemeSummaryCard({ item, index }: { item: EligibilitySummary; index: number }) {
  const cfg = STATUS_CONFIG[item.status];
  const Icon = cfg.icon;
  const barWidth = `${Math.round(item.score)}%`;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.03 }}>
      <Link href={`/eligibility?scheme=${item.scheme_id}`} className="block group">
        <Card className="hover:shadow-md hover:border-primary/30 transition-all group-hover:-translate-y-0.5 duration-200">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-mono text-muted-foreground">{item.scheme_code}</p>
                <p className="text-sm font-semibold line-clamp-1 group-hover:text-primary transition-colors">{item.scheme_name}</p>
                {item.ministry && <p className="text-xs text-muted-foreground truncate mt-0.5">{item.ministry}</p>}
              </div>
              <div className={cn("flex items-center gap-1 shrink-0 text-xs font-medium", cfg.colour)}>
                <Icon className="h-3.5 w-3.5" />
                {cfg.label}
              </div>
            </div>

            {/* Score bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Score</span>
                <span>{Math.round(item.score)}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    item.score === 100 ? "bg-green-500" : item.score >= 50 ? "bg-yellow-500" : "bg-red-500"
                  )}
                  style={{ width: barWidth }}
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{item.passed_count}/{item.total_rules} criteria passed</span>
              <span className="flex items-center gap-1 text-primary group-hover:gap-1.5 transition-all">
                Check details <ArrowRight className="h-3 w-3" />
              </span>
            </div>
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  );
}

function MyEligibilityContent() {
  const { data, isLoading } = useMyEligibility();

  const stats = data ? [
    { label: "Eligible", value: data.eligible_count, colour: "text-green-600" },
    { label: "Not Eligible", value: data.not_eligible_count, colour: "text-red-600" },
    { label: "Incomplete", value: data.incomplete_count, colour: "text-yellow-600" },
    { label: "Profile", value: `${Math.round(data.profile_completion)}%`, colour: "text-primary" },
  ] : [];

  return (
    <div className="page-container py-8 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">My Eligibility</h1>
          <p className="text-muted-foreground mt-1">See all schemes and your eligibility status.</p>
        </div>
        <Link href="/profile" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors">
          <User className="h-4 w-4" />Complete Profile
        </Link>
      </div>

      {/* Stats row */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
        </div>
      ) : data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {stats.map((s) => (
            <Card key={s.label}>
              <CardContent className="p-4 text-center">
                <p className={cn("text-2xl font-bold", s.colour)}>{s.value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Profile completion bar */}
      {data && data.profile_completion < 100 && (
        <Card className="border-yellow-200 dark:border-yellow-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Profile Completion</span>
              <span className="text-sm text-yellow-600 font-bold">{Math.round(data.profile_completion)}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
              <div className="h-full rounded-full bg-yellow-500 transition-all duration-700" style={{ width: `${data.profile_completion}%` }} />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Complete your profile to unlock accurate eligibility checks.{" "}
              <Link href="/profile" className="text-primary hover:underline">Update now →</Link>
            </p>
          </CardContent>
        </Card>
      )}

      {/* Scheme list */}
      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40 rounded-xl" />)}
        </div>
      ) : data?.data.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-muted-foreground">No schemes with eligibility rules found.</CardContent></Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data?.data.map((item, i) => <SchemeSummaryCard key={item.scheme_id} item={item} index={i} />)}
        </div>
      )}
    </div>
  );
}

export default function MyEligibilityPage() {
  return (
    <ProtectedRoute>
      <MainLayout><MyEligibilityContent /></MainLayout>
    </ProtectedRoute>
  );
}
