import { MainLayout } from "@/components/layout/MainLayout";
import { PlaceholderPage } from "@/components/common/PlaceholderPage";

import { getTranslations } from "next-intl/server";
import { useTranslations } from "next-intl";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "metadata" });
  return {
    title: t("chat_title"),
    description: t("chat_desc"),
  };
}

export default function ChatPage() {
  const t = useTranslations("chat");
  return (
    <MainLayout>
      <PlaceholderPage
        title={t("title")}
        description={t("description")}
        phase="Phase 4 — AI & RAG"
      />
    </MainLayout>
  );
}
