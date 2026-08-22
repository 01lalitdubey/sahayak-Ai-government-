"use client";

import { motion } from "framer-motion";
import { Landmark } from "lucide-react";
import { useTranslations } from "next-intl";

export function LoadingScreen() {
  const t = useTranslations("common");
  return (
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-background">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="flex flex-col items-center gap-4"
      >
        <div className="relative">
          <Landmark className="h-12 w-12 text-primary" />
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-primary"
            animate={{ scale: [1, 1.4, 1], opacity: [1, 0, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        </div>
        <p className="text-sm text-muted-foreground">{t("loading")}</p>
      </motion.div>
    </div>
  );
}
