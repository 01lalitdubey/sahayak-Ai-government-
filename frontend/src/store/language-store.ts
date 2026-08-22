import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Locale } from "@/i18n/routing";

export interface LanguageInfo {
  code: Locale;
  nativeName: string;
}

export const AVAILABLE_LANGUAGES: LanguageInfo[] = [
  { code: "en", nativeName: "English" },
  { code: "hi", nativeName: "हिन्दी" },
  { code: "ta", nativeName: "தமிழ்" },
  { code: "te", nativeName: "తెలుగు" },
  { code: "mr", nativeName: "मराठी" },
  { code: "gu", nativeName: "ગુજરાતી" },
  { code: "bn", nativeName: "বাংলা" },
  { code: "kn", nativeName: "ಕನ್ನಡ" },
  { code: "ml", nativeName: "മലയാളം" },
  { code: "pa", nativeName: "ਪੰਜਾਬੀ" },
  { code: "or", nativeName: "ଓଡ଼ିଆ" },
  { code: "as", nativeName: "অসমীয়া" },
];

interface LanguageState {
  currentLanguage: Locale;
  availableLanguages: LanguageInfo[];
  setLanguage: (lang: Locale) => void;
  initializeLanguage: (lang: Locale) => void;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      currentLanguage: "en",
      availableLanguages: AVAILABLE_LANGUAGES,
      setLanguage: (lang: Locale) => set({ currentLanguage: lang }),
      initializeLanguage: (lang: Locale) => set({ currentLanguage: lang }),
    }),
    {
      name: "language-storage",
      // only store the currentLanguage, not the whole availableLanguages array
      partialize: (state) => ({ currentLanguage: state.currentLanguage }),
    }
  )
);
