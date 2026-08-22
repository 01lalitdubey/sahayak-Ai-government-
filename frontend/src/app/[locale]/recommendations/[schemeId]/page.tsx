"use client";

import { use } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Info,
  FileText,
  Phone,
  Mail,
  Calendar,
  MapPin,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RecommendationScore } from "@/components/recommendations/RecommendationScore";
import { PriorityBadge } from "@/components/recommendations/PriorityBadge";
import { RecommendationReasonList } from "@/components/recommendations/RecommendationReasonList";
import { useRecommendation } from "@/hooks/use-recommendations";
import { ROUTES } from "@/lib/constants";
import { formatDate } from "@/lib/utils";

interface PageProps {
  params: Promise<{ schemeId: string }>;
}

function DetailSkeleton() {
  return (
    <div className="page-container py-8 space-y-6">
      <div className="h-4 w-24 bg-muted rounded animate-pulse" />
      <div className="h-8 w-64 bg-muted rounded animate-pulse" />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-32 w-full bg-muted rounded-lg animate-pulse" />
          ))}
        </div>
        <div className="lg:col-span-2 space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 w-full bg-muted rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

function DetailContent({ schemeId }: { schemeId: string }) {
  const { data: rec, isLoading, isError } = useRecommendation(schemeId);

  if (isLoading) return <DetailSkeleton />;

  if (isError || !rec) {
    return (
      <div className="page-container py-20 flex flex-col items-center gap-4 text-center">
        <XCircle className="h-14 w-14 text-muted-foreground/30" />
        <h2 className="text-lg font-semibold">Recommendation Not Found</h2>
        <p className="text-sm text-muted-foreground">
          This scheme may not be available or you may not have a profile yet.
        </p>
        <Button variant="outline" asChild>
          <Link href={ROUTES.RECOMMENDATIONS}>
            <ArrowLeft className="h-4 w-4 mr-1.5" /> Back to Recommendations
          </Link>
        </Button>
      </div>
    );
  }

  const scoreBreakdown = rec.score_breakdown;

  return (
    <div className="page-container py-8 space-y-6">
      {/* Back nav */}
      <Button variant="ghost" size="sm" className="h-8 px-2 text-muted-foreground" asChild>
        <Link href={ROUTES.RECOMMENDATIONS}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Recommendations
        </Link>
      </Button>

      {/* Page title */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <PriorityBadge priority={rec.priority} size="md" />
          {rec.is_featured && (
            <Badge variant="secondary" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
              ⭐ Featured
            </Badge>
          )}
          {rec.eligible && (
            <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
              ✓ Eligible
            </Badge>
          )}
        </div>
        <p className="text-xs font-mono text-muted-foreground">{rec.scheme_code}</p>
        <h1 className="text-2xl font-bold mt-1">{rec.scheme_name}</h1>
        <div className="flex flex-wrap gap-3 mt-2 text-sm text-muted-foreground">
          {rec.ministry && <span>🏛 {rec.ministry}</span>}
          {rec.state ? (
            <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{rec.state}</span>
          ) : (
            <span className="text-blue-500">🌐 All States</span>
          )}
        </div>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column — score + apply */}
        <div className="space-y-4">
          {/* Score card */}
          <Card>
            <CardContent className="p-5 flex flex-col items-center gap-4">
              <RecommendationScore score={rec.recommendation_score} size="lg" />
              <div className="w-full space-y-2">
                {[
                  { label: "Eligibility", val: scoreBreakdown.eligibility_score, max: 40 },
                  { label: "Occupation", val: scoreBreakdown.occupation_score, max: 20 },
                  { label: "Income", val: scoreBreakdown.income_score, max: 15 },
                  { label: "State", val: scoreBreakdown.state_score, max: 10 },
                  { label: "Category", val: scoreBreakdown.category_score, max: 10 },
                  { label: "Featured", val: scoreBreakdown.featured_score, max: 5 },
                ].map(({ label, val, max }) => (
                  <div key={label} className="flex items-center gap-2 text-xs">
                    <span className="w-20 text-muted-foreground shrink-0">{label}</span>
                    <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary/70 transition-all duration-500"
                        style={{ width: `${(val / max) * 100}%` }}
                      />
                    </div>
                    <span className="w-12 text-right font-medium">
                      {val.toFixed(0)}/{max}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Apply button */}
          {rec.official_url && (
            <Button className="w-full" asChild>
              <a href={rec.official_url} target="_blank" rel="noopener noreferrer">
                Apply Now <ExternalLink className="h-4 w-4 ml-1.5" />
              </a>
            </Button>
          )}

          {/* Contact */}
          {(rec.contact_email || rec.contact_phone) && (
            <Card>
              <CardContent className="p-4 space-y-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Contact</p>
                {rec.contact_email && (
                  <a href={`mailto:${rec.contact_email}`} className="flex items-center gap-2 text-xs hover:text-primary transition-colors">
                    <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                    {rec.contact_email}
                  </a>
                )}
                {rec.contact_phone && (
                  <a href={`tel:${rec.contact_phone}`} className="flex items-center gap-2 text-xs hover:text-primary transition-colors">
                    <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                    {rec.contact_phone}
                  </a>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column — details */}
        <div className="lg:col-span-2 space-y-4">
          {/* Why recommended */}
          <Card>
            <CardHeader className="pb-2">
              <h2 className="font-semibold text-sm">Why This Is Recommended For You</h2>
            </CardHeader>
            <CardContent>
              <RecommendationReasonList reasons={rec.reasons} />
            </CardContent>
          </Card>

          {/* Missing info */}
          {rec.missing_information.length > 0 && (
            <Card className="border-amber-500/20">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-sm mb-1">Profile Information Missing</p>
                    <p className="text-xs text-muted-foreground mb-2">
                      Completing these fields may improve your score:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {rec.missing_information.map((m) => (
                        <Badge key={m} variant="outline" className="text-xs border-amber-500/30">
                          {m}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Eligibility breakdown */}
          {(rec.passed_rules.length > 0 || rec.failed_rules.length > 0) && (
            <Card>
              <CardHeader className="pb-2">
                <h2 className="font-semibold text-sm">Eligibility Breakdown</h2>
              </CardHeader>
              <CardContent className="space-y-2">
                {rec.passed_rules.map((r, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-xs">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-medium">{r.criterion}</span>
                      <span className="text-muted-foreground"> — {r.reason}</span>
                    </div>
                  </div>
                ))}
                {rec.failed_rules.map((r, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-xs">
                    <XCircle className="h-3.5 w-3.5 text-rose-500 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-medium">{r.criterion}</span>
                      <span className="text-muted-foreground"> — {r.reason}</span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Scheme description */}
          {(rec.full_description || rec.short_description) && (
            <Card>
              <CardHeader className="pb-2">
                <h2 className="font-semibold text-sm flex items-center gap-2">
                  <Info className="h-4 w-4 text-muted-foreground" /> About This Scheme
                </h2>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {rec.full_description || rec.short_description}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Benefits */}
          {rec.benefits && (
            <Card>
              <CardHeader className="pb-2">
                <h2 className="font-semibold text-sm flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Benefits
                </h2>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">{rec.benefits}</p>
              </CardContent>
            </Card>
          )}

          {/* Application details */}
          <Card>
            <CardContent className="p-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Application Mode</p>
                <p className="font-medium capitalize">{rec.application_mode}</p>
              </div>
              {rec.application_start_date && (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Opens</p>
                  <p className="font-medium flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    {formatDate(rec.application_start_date)}
                  </p>
                </div>
              )}
              {rec.application_end_date && (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Closes</p>
                  <p className="font-medium flex items-center gap-1 text-rose-600">
                    <Calendar className="h-3.5 w-3.5" />
                    {formatDate(rec.application_end_date)}
                  </p>
                </div>
              )}
              {rec.official_pdf_url && (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Guidelines</p>
                  <a
                    href={rec.official_pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium text-primary flex items-center gap-1 hover:underline text-sm"
                  >
                    <FileText className="h-3.5 w-3.5" /> PDF
                  </a>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function RecommendationDetailPage({ params }: PageProps) {
  const { schemeId } = use(params);
  return <DetailContent schemeId={schemeId} />;
}
