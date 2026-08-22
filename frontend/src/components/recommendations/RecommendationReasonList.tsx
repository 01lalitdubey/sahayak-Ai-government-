/**
 * RecommendationReasonList — Sahayak AI (Phase 5)
 * Renders a list of recommendation reasons with type-specific icons.
 */

import type React from "react";
import {
  CheckCircle2,
  Briefcase,
  Wallet,
  MapPin,
  Users,
  Star,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { RecommendationReason, RecommendationReasonType } from "@/types/recommendation";

interface RecommendationReasonListProps {
  reasons: RecommendationReason[];
  className?: string;
  compact?: boolean;
}

const REASON_ICON: Record<RecommendationReasonType, React.ElementType> = {
  eligibility: CheckCircle2,
  occupation: Briefcase,
  income: Wallet,
  state: MapPin,
  category: Users,
  featured: Star,
  general: Info,
};

const REASON_COLOR: Record<RecommendationReasonType, string> = {
  eligibility: "text-emerald-500 bg-emerald-500/10",
  occupation: "text-blue-500 bg-blue-500/10",
  income: "text-violet-500 bg-violet-500/10",
  state: "text-orange-500 bg-orange-500/10",
  category: "text-pink-500 bg-pink-500/10",
  featured: "text-yellow-500 bg-yellow-500/10",
  general: "text-slate-500 bg-slate-500/10",
};

export function RecommendationReasonList({
  reasons,
  className,
  compact = false,
}: RecommendationReasonListProps) {
  if (!reasons.length) return null;

  return (
    <ul className={cn("space-y-2", className)} aria-label="Why this is recommended">
      {reasons.map((reason, i) => {
        const Icon = REASON_ICON[reason.reason_type] ?? Info;
        const colorCls = REASON_COLOR[reason.reason_type] ?? REASON_COLOR.general;
        return (
          <li
            key={i}
            className={cn(
              "flex items-start gap-2.5",
              compact ? "text-xs" : "text-sm"
            )}
          >
            <span
              className={cn(
                "mt-0.5 flex shrink-0 items-center justify-center rounded-full",
                compact ? "h-5 w-5" : "h-6 w-6",
                colorCls
              )}
            >
              <Icon className={compact ? "h-2.5 w-2.5" : "h-3 w-3"} />
            </span>
            <span className="text-muted-foreground leading-relaxed">{reason.text}</span>
          </li>
        );
      })}
    </ul>
  );
}
