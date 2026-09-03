import { MainLayout } from "@/components/layout/MainLayout";
import { getTranslations } from "next-intl/server";

import { ChatClient } from "./ChatClient";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "metadata" });
  return {
    title: t("chat_title"),
    description: t("chat_desc"),
  };
}

export default function ChatPage() {
  return (
    <MainLayout>
      <ChatClient />
    </MainLayout>
  );
}
