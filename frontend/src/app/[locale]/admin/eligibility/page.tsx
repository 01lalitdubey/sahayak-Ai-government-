"use client";

import { useState } from "react";
import { Trash2, Plus, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { MainLayout } from "@/components/layout/MainLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useEligibilityRules, useCreateRule, useDeleteRule } from "@/hooks/use-eligibility";
import { useSchemes } from "@/hooks/use-schemes";
import { showToast } from "@/components/ui/toast-utils";
import { formatDate } from "@/lib/utils";
import type { EligibilityRuleCreatePayload } from "@/types/eligibility";
import { useTranslations } from "next-intl";

function RuleForm({ onSubmit }: { onSubmit: (d: EligibilityRuleCreatePayload) => Promise<void> }) {
  const t = useTranslations("admin");
  const { data: schemesData } = useSchemes({ page_size: 100 });
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<EligibilityRuleCreatePayload>();

  async function handle(data: EligibilityRuleCreatePayload) {
    const clean = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "" && v !== null && v !== undefined && v !== 0)
    ) as EligibilityRuleCreatePayload;
    await onSubmit(clean);
    reset();
  }

  return (
    <form onSubmit={handleSubmit(handle)} className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-sm">{t("scheme_label")}</Label>
        <select className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring" {...register("scheme_id", { required: true })}>
          <option value="">{t("select_scheme")}</option>
          {schemesData?.data.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { name: "minimum_age", label: t("min_age") },
          { name: "maximum_age", label: t("max_age") },
          { name: "minimum_income", label: t("min_income") },
          { name: "maximum_income", label: t("max_income") },
        ].map(({ name, label }) => (
          <div key={name} className="space-y-1.5">
            <Label className="text-xs">{label}</Label>
            <Input type="number" placeholder="Any" {...register(name as keyof EligibilityRuleCreatePayload)} />
          </div>
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { name: "gender", label: t("gender"), options: ["", "male", "female", "other"] },
          { name: "occupation", label: t("occupation"), options: ["", "farmer", "agricultural_labourer", "self_employed", "salaried", "student", "unemployed", "other"] },
          { name: "category", label: t("category"), options: ["", "general", "obc", "sc", "st", "ews"] },
        ].map(({ name, label, options }) => (
          <div key={name} className="space-y-1.5">
            <Label className="text-xs">{label}</Label>
            <select className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring" {...register(name as keyof EligibilityRuleCreatePayload)}>
              {options.map((o) => <option key={o} value={o}>{o ? t(o as Parameters<typeof t>[0]) || o : t("any")}</option>)}
            </select>
          </div>
        ))}
      </div>
      <div className="space-y-1.5">
        <Label className="text-xs">{t("state")}</Label>
        <Input placeholder={t("any_state_placeholder")} {...register("state")} />
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />{t("creating")}</> : <><Plus className="h-4 w-4 mr-2" />{t("add_rule")}</>}
      </Button>
    </form>
  );
}

function AdminEligibilityContent() {
  const t = useTranslations("admin");
  const [filterSchemeId, setFilterSchemeId] = useState<string>("");
  const { data: schemesData } = useSchemes({ page_size: 100 });
  const { data: rulesData, isLoading } = useEligibilityRules(filterSchemeId || undefined);
  const createMut = useCreateRule();
  const deleteMut = useDeleteRule();

  async function handleCreate(payload: EligibilityRuleCreatePayload) {
    try {
      await createMut.mutateAsync(payload);
      showToast(t("rule_created"), "success");
    } catch { showToast(t("rule_create_failed"), "error"); }
  }

  async function handleDelete(id: string) {
    if (!confirm(t("delete_rule_confirm"))) return;
    try {
      await deleteMut.mutateAsync(id);
      showToast(t("rule_deleted"), "success");
    } catch { showToast(t("delete_failed"), "error"); }
  }

  return (
    <div className="page-container py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("manage_rules")}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t("rules_count", { count: rulesData?.total ?? 0 })}</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">{t("add_rule_title")}</CardTitle></CardHeader>
        <CardContent><RuleForm onSubmit={handleCreate} /></CardContent>
      </Card>

      {/* Filter */}
      <div className="flex items-center gap-3">
        <Label className="text-sm shrink-0">{t("filter_scheme")}</Label>
        <select
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          value={filterSchemeId}
          onChange={(e) => setFilterSchemeId(e.target.value)}
        >
          <option value="">{t("all_schemes")}</option>
          {schemesData?.data.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </div>

      {/* Rules table */}
      <div className="rounded-lg border overflow-x-auto">
        {isLoading ? (
          <div className="p-4 space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !rulesData?.data.length ? (
          <div className="p-12 text-center text-muted-foreground">{t("no_rules")}</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                {[t("scheme"), t("age"), t("income"), t("gender"), t("occupation"), t("state"), t("category"), t("created"), ""].map((h) => (
                  <th key={h} className="text-left font-medium px-3 py-2.5 text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rulesData.data.map((rule) => {
                const scheme = schemesData?.data.find((s) => s.id === rule.scheme_id);
                return (
                  <tr key={rule.id} className="border-b last:border-0 hover:bg-muted/30">
                    <td className="px-3 py-2 text-xs font-medium max-w-[150px] truncate">{scheme?.name ?? rule.scheme_id.slice(0, 8)}</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {rule.minimum_age || rule.maximum_age ? `${rule.minimum_age ?? "∞"}–${rule.maximum_age ?? "∞"}` : "–"}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {rule.minimum_income || rule.maximum_income ? `₹${(rule.minimum_income ?? 0).toLocaleString()}–₹${(rule.maximum_income ?? "∞").toLocaleString()}` : "–"}
                    </td>
                    <td className="px-3 py-2 text-xs capitalize">{rule.gender ? t(rule.gender as Parameters<typeof t>[0]) || rule.gender : "–"}</td>
                    <td className="px-3 py-2 text-xs capitalize">{rule.occupation ? t(rule.occupation as Parameters<typeof t>[0]) || rule.occupation.replace(/_/g, " ") : "–"}</td>
                    <td className="px-3 py-2 text-xs">{rule.state ?? t("all_india")}</td>
                    <td className="px-3 py-2 text-xs uppercase">{rule.category ? t(rule.category as Parameters<typeof t>[0]) || rule.category : "–"}</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">{formatDate(rule.created_at)}</td>
                    <td className="px-3 py-2">
                      <Button variant="ghost" size="icon" className="h-7 w-7 hover:text-destructive" onClick={() => handleDelete(rule.id)} title={t("delete")}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default function AdminEligibilityPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <MainLayout><AdminEligibilityContent /></MainLayout>
    </ProtectedRoute>
  );
}
