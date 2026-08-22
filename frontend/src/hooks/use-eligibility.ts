"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { eligibilityService } from "@/services/eligibility.service";
import type { EligibilityRuleCreatePayload } from "@/types/eligibility";
import { useLocale } from "next-intl";

export const ELIGIBILITY_KEYS = {
  mySchemes: (locale: string) => ["eligibility", "my-schemes", locale] as const,
  check: (locale: string, id: string) => ["eligibility", "check", id, locale] as const,
  rules: (schemeId?: string) => ["eligibility", "rules", schemeId ?? "all"] as const, // Rules are admin side, no need for locale caching usually
};

export function useMyEligibility() {
  const locale = useLocale();
  return useQuery({
    queryKey: ELIGIBILITY_KEYS.mySchemes(locale),
    queryFn: () => eligibilityService.getMySchemes(),
    staleTime: 1000 * 60 * 2,
  });
}

export function useEligibility(schemeId: string | null) {
  const locale = useLocale();
  return useQuery({
    queryKey: ELIGIBILITY_KEYS.check(locale, schemeId ?? ""),
    queryFn: () => eligibilityService.getEligibility(schemeId!),
    enabled: !!schemeId,
    staleTime: 1000 * 60 * 2,
  });
}

export function useCheckEligibility() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (schemeId: string) => eligibilityService.checkEligibility(schemeId),
    onSuccess: () => {
      // Invalidate all eligibility checks across all locales
      qc.invalidateQueries({ queryKey: ["eligibility", "check"] });
    },
  });
}

export function useEligibilityRules(schemeId?: string) {
  return useQuery({
    queryKey: ELIGIBILITY_KEYS.rules(schemeId),
    queryFn: () => eligibilityService.getRules(schemeId),
    staleTime: 1000 * 60 * 5,
  });
}

export function useCreateRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: EligibilityRuleCreatePayload) => eligibilityService.createRule(p),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["eligibility", "rules"] }),
  });
}

export function useDeleteRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => eligibilityService.deleteRule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["eligibility", "rules"] }),
  });
}
