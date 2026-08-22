/**
 * PlaceholderPage — Sahayak AI
 * Generic placeholder rendered inside every not-yet-implemented page.
 * Shows page name, description, and an "under construction" indicator.
 */

import { Construction } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "./PageHeader";
import { useTranslations } from "next-intl";

interface PlaceholderPageProps {
  title: string;
  description: string;
  phase?: string;
}

export function PlaceholderPage({
  title,
  description,
  phase,
}: PlaceholderPageProps) {
  const t = useTranslations("common");
  const displayPhase = phase || t("coming_soon");

  return (
    <section className="page-container section-padding">
      <PageHeader title={title} description={description}>
        <Badge variant="secondary" className="w-fit">
          {displayPhase}
        </Badge>
      </PageHeader>

      <Card className="mt-10 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-muted-foreground">
            <Construction className="h-5 w-5" aria-hidden="true" />
            {t("under_construction")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {t("placeholder_desc")}
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
