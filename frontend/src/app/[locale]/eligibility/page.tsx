"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle, AlertCircle, Loader2, Search, Info } from "lucide-react";
import { MainLayout } from "@/components/layout/MainLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useSchemes } from "@/hooks/use-schemes";
import { useCheckEligibility } from "@/hooks/use-eligibility";
import { showToast } from "@/components/ui/toast-utils";
import { cn } from "@/lib/utils";
import type { EligibilityCheckResponse, RuleResult } from "@/types/eligibility";
import { useTranslations } from "next-intl";

function ScoreCircle({ score }: { score: number }) {
  const colour = score === 100 ? "text-green-500" : score >= 50 ? "text-yellow-500" : "text-red-500";
  return (
    <div className={cn("flex flex-col items-center gap-1", colour)}>
      <span className="text-5xl font-bold">{Math.round(score)}</span>
      <span className="text-sm text-muted-foreground">/ 100</span>
      <span className="text-xs font-medium">{useTranslations("eligibility")("score")}</span>
    </div>
  );
}

function RuleRow({ rule }: { rule: RuleResult }) {
  const Icon = rule.passed ? CheckCircle2 : rule.user_value === "Not provided" ? AlertCircle : XCircle;
  const colour = rule.passed ? "text-green-600" : rule.user_value === "Not provided" ? "text-yellow-600" : "text-red-600";
  return (
    <div className="flex items-start gap-3 py-2.5 border-b last:border-0">
      <Icon className={cn("h-4 w-4 mt-0.5 shrink-0", colour)} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{rule.criterion}</p>
        <p className="text-xs text-muted-foreground">{rule.reason}</p>
      </div>
      <Badge variant="outline" className="text-xs shrink-0">{rule.requirement}</Badge>
    </div>
  );
}

function EligibilityResult({ result }: { result: EligibilityCheckResponse }) {
  const t = useTranslations("eligibility");
  const statusConfig = {
    eligible: { label: t("eligible"), colour: "text-green-600", bg: "bg-green-50 border-green-200 dark:bg-green-900/20" },
    not_eligible: { label: t("not_eligible"), colour: "text-red-600", bg: "bg-red-50 border-red-200 dark:bg-red-900/20" },
    incomplete_profile: { label: t("incomplete"), colour: "text-yellow-600", bg: "bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20" },
    no_rules: { label: t("no_rules"), colour: "text-muted-foreground", bg: "bg-muted border-border" },
  }[result.status];

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      {/* Status banner */}
      <div className={cn("rounded-xl border p-6 text-center space-y-3", statusConfig.bg)}>
        <p className={cn("text-2xl font-bold", statusConfig.colour)}>{statusConfig.label}</p>
        <p className="text-sm text-muted-foreground">{result.scheme_name}</p>
        <ScoreCircle score={result.score} />
        <div className="flex justify-center gap-4 text-xs text-muted-foreground">
          <span className="text-green-600">✓ {t("passed", { count: result.passed_count })}</span>
          <span className="text-red-600">✗ {t("failed", { count: result.failed_count })}</span>
          {result.missing_count > 0 && <span className="text-yellow-600">⚠ {t("missing", { count: result.missing_count })}</span>}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Passed rules */}
        {result.passed_rules.length > 0 && (
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm text-green-600">✓ {t("passed_criteria")}</CardTitle></CardHeader>
            <CardContent className="pt-0">{result.passed_rules.map((r, i) => <RuleRow key={i} rule={r} />)}</CardContent>
          </Card>
        )}
        {/* Failed rules */}
        {result.failed_rules.length > 0 && (
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm text-red-600">✗ {t("failed_criteria")}</CardTitle></CardHeader>
            <CardContent className="pt-0">{result.failed_rules.map((r, i) => <RuleRow key={i} rule={r} />)}</CardContent>
          </Card>
        )}
      </div>

      {/* Missing info */}
      {result.missing_information.length > 0 && (
        <Card className="border-yellow-200 dark:border-yellow-800">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-yellow-600 flex items-center gap-2"><Info className="h-4 w-4" />{t("missing_info")}</CardTitle></CardHeader>
          <CardContent className="pt-0">
            <ul className="space-y-1">
              {result.missing_information.map((m, i) => (
                <li key={i} className="text-sm text-muted-foreground flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-yellow-500 shrink-0" />{m}
                </li>
              ))}
            </ul>
            <p className="text-xs text-muted-foreground mt-3">{t("complete_profile_assessment")}</p>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}

function EligibilityContent() {
  const t = useTranslations("eligibility");
  const tCommon = useTranslations("common");
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>("");
  const [result, setResult] = useState<EligibilityCheckResponse | null>(null);
  const { data: schemesData, isLoading: loadingSchemes } = useSchemes({ page_size: 100 });
  const checkMut = useCheckEligibility();

  async function handleCheck() {
    if (!selectedSchemeId) return;
    try {
      const res = await checkMut.mutateAsync(selectedSchemeId);
      setResult(res);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      showToast(msg ?? t("check_failed"), "error");
    }
  }

  return (
    <div className="page-container py-8 max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t("title")}</h1>
        <p className="text-muted-foreground mt-1">{t("subtitle")}</p>
      </div>

      <Card>
        <CardContent className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="scheme-select">{t("select_scheme")}</label>
            <select
              id="scheme-select"
              className="w-full h-10 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              value={selectedSchemeId}
              onChange={(e) => { setSelectedSchemeId(e.target.value); setResult(null); }}
              aria-label={t("select_scheme")}
            >
              <option value="">{t("select_scheme_placeholder")}</option>
              {loadingSchemes ? <option disabled>{tCommon("loading")}</option> :
                schemesData?.data.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.scheme_code})</option>
                ))}
            </select>
          </div>
          <Button onClick={handleCheck} disabled={!selectedSchemeId || checkMut.isPending} className="w-full">
            {checkMut.isPending ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />{t("checking")}</> : <><Search className="h-4 w-4 mr-2" />{t("check_button")}</>}
          </Button>
        </CardContent>
      </Card>

      <AnimatePresence>
        {result && <EligibilityResult result={result} />}
      </AnimatePresence>
    </div>
  );
}

export default function EligibilityPage() {
  return (
    <ProtectedRoute>
      <MainLayout><EligibilityContent /></MainLayout>
    </ProtectedRoute>
  );
}
