import { getTranslations } from "next-intl/server";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "metadata" });
  return {
    title: t("eligibility_title"),
    description: t("eligibility_desc"),
  };
}

export default function EligibilityLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
