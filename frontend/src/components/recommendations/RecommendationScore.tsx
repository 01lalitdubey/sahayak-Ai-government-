/**
 * RecommendationScore — Sahayak AI (Phase 5)
 * Circular score display with color gradient and animated fill.
 */

"use client";

import { cn } from "@/lib/utils";

interface RecommendationScoreProps {
  score: number; // 0–100
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

function scoreColor(score: number): string {
  if (score >= 90) return "text-emerald-500";
  if (score >= 70) return "text-amber-500";
  return "text-slate-400";
}

function ringColor(score: number): string {
  if (score >= 90) return "stroke-emerald-500";
  if (score >= 70) return "stroke-amber-500";
  return "stroke-slate-400";
}

const SIZE_CONFIG = {
  sm: { container: "h-14 w-14", text: "text-base", label: "text-[9px]", r: 22, stroke: 4 },
  md: { container: "h-20 w-20", text: "text-xl", label: "text-[10px]", r: 32, stroke: 5 },
  lg: { container: "h-28 w-28", text: "text-3xl", label: "text-xs", r: 44, stroke: 6 },
};

export function RecommendationScore({
  score,
  size = "md",
  showLabel = true,
  className,
}: RecommendationScoreProps) {
  const cfg = SIZE_CONFIG[size];
  const circumference = 2 * Math.PI * cfg.r;
  const dashOffset = circumference - (score / 100) * circumference;
  const viewBox = cfg.r * 2 + cfg.stroke * 2;
  const center = cfg.r + cfg.stroke;

  return (
    <div
      className={cn("relative flex items-center justify-center", cfg.container, className)}
      aria-label={`Recommendation score: ${score.toFixed(0)} out of 100`}
    >
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${viewBox} ${viewBox}`}
        className="-rotate-90"
      >
        {/* Background ring */}
        <circle
          cx={center}
          cy={center}
          r={cfg.r}
          fill="none"
          stroke="currentColor"
          strokeWidth={cfg.stroke}
          className="text-muted/30"
        />
        {/* Score ring */}
        <circle
          cx={center}
          cy={center}
          r={cfg.r}
          fill="none"
          strokeWidth={cfg.stroke}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          className={cn("transition-all duration-700 ease-out", ringColor(score))}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("font-bold leading-none", cfg.text, scoreColor(score))}>
          {Math.round(score)}
        </span>
        {showLabel && (
          <span className={cn("text-muted-foreground uppercase tracking-wider mt-0.5", cfg.label)}>
            score
          </span>
        )}
      </div>
    </div>
  );
}
