/**
 * Home Page (/) — Sahayak AI
 * Landing page with hero section and feature highlights.
 */

import Link from "next/link";
import { useTranslations } from "next-intl";
import { getTranslations } from "next-intl/server";
import { ArrowRight, Landmark, Search, MessageSquare, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MainLayout } from "@/components/layout/MainLayout";
import { ROUTES } from "@/lib/constants";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "metadata" });
  return {
    title: t("home_title"),
    description: t("home_desc"),
  };
}

export default function HomePage() {
  const t = useTranslations("landing");

  const FEATURES = [
    {
      icon: Search,
      title: t("feat_discover_title"),
      description: t("feat_discover_desc"),
    },
    {
      icon: CheckCircle,
      title: t("feat_check_title"),
      description: t("feat_check_desc"),
    },
    {
      icon: MessageSquare,
      title: t("feat_chat_title"),
      description: t("feat_chat_desc"),
    },
  ];

  return (
    <MainLayout>
      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="page-container section-padding text-center">
        <div className="mx-auto max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border bg-muted px-4 py-1.5 text-sm text-muted-foreground">
            <Landmark className="h-4 w-4 text-primary" />
            {t("badge")}
          </div>
          <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            {t("title_start")}{" "}
            <span className="text-gradient">{t("title_highlight")}</span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground sm:text-xl">
            {t("subtitle")}
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Button size="lg" asChild>
              <Link href={ROUTES.REGISTER}>
                {t("get_started")} <ArrowRight className="h-4 w-4 ml-2" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href={ROUTES.SCHEMES}>{t("browse_schemes")}</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section className="page-container pb-16">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <Card key={title} className="transition-shadow hover:shadow-md">
              <CardHeader>
                <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <Icon className="h-5 w-5 text-primary" aria-hidden="true" />
                </div>
                <CardTitle className="text-lg">{title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </MainLayout>
  );
}
