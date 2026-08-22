import { useLocale } from "next-intl";
import { useLanguageStore } from "@/store/language-store";
import type { Locale } from "@/i18n/routing";
import { usePathname, useRouter } from "@/i18n/routing";
import { useEffect, useTransition } from "react";

export function useLanguage() {
  const currentLocale = useLocale() as Locale;
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();

  const { currentLanguage, availableLanguages, setLanguage, initializeLanguage } = useLanguageStore();

  // Sync zustand store with current locale from URL on mount
  useEffect(() => {
    if (currentLocale !== currentLanguage) {
      initializeLanguage(currentLocale);
    }
  }, [currentLocale, currentLanguage, initializeLanguage]);

  const changeLanguage = (newLocale: Locale) => {
    if (newLocale === currentLocale) return;

    setLanguage(newLocale);

    // Navigate to the new locale while preserving the current pathname
    startTransition(() => {
      router.replace(pathname, { locale: newLocale });
    });
  };

  return {
    currentLanguage: currentLocale,
    availableLanguages,
    changeLanguage,
    isPending,
  };
}
