import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useTranslations } from "next-intl";
import { MainLayout } from "@/components/layout/MainLayout";
import { ROUTES } from "@/lib/constants";

export default function NotFound() {
  const t = useTranslations("errors");
  return (
    <MainLayout>
      <section className="page-container section-padding text-center">
        <p className="text-6xl font-bold text-primary">404</p>
        <h1 className="mt-4 text-3xl font-bold">{t("404_title")}</h1>
        <p className="mt-3 text-muted-foreground">
          {t("404_desc")}
        </p>
        <Button className="mt-8" asChild>
          <Link href={ROUTES.DASHBOARD}>{t("back_home")}</Link>
        </Button>
      </section>
    </MainLayout>
  );
}
