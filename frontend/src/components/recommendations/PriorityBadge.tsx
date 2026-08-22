/**
 * PriorityBadge — Sahayak AI (Phase 5)
 * Displays recommendation priority level (HIGH/MEDIUM/LOW) with color coding.
 */

import { cn } from "@/lib/utils";
import type { RecommendationPriority } from "@/types/recommendation";

interface PriorityBadgeProps {
  priority: RecommendationPriority;
  size?: "sm" | "md";
  className?: string;
}

const CONFIG: Record<
  RecommendationPriority,
  { label: string; dot: string; badge: string }
> = {
  HIGH: {
    label: "High Priority",
    dot: "bg-emerald-500",
    badge:
      "bg-emerald-500/10 text-emerald-600 border-emerald-500/20 dark:text-emerald-400",
  },
  MEDIUM: {
    label: "Medium Priority",
    dot: "bg-amber-500",
    badge:
      "bg-amber-500/10 text-amber-600 border-amber-500/20 dark:text-amber-400",
  },
  LOW: {
    label: "Low Priority",
    dot: "bg-slate-400",
    badge:
      "bg-slate-500/10 text-slate-500 border-slate-400/20 dark:text-slate-400",
  },
};

export function PriorityBadge({
  priority,
  size = "sm",
  className,
}: PriorityBadgeProps) {
  const cfg = CONFIG[priority];
  return (
    <span
      aria-label={cfg.label}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-medium",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        cfg.badge,
        className
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dot)} />
      {priority}
    </span>
  );
}
