"use client";

import { useState, useRef, useEffect } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Globe, ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Locale } from "@/i18n/routing";
import { useTranslations } from "next-intl";

export function LanguageSwitcher() {
  const t = useTranslations("ui");
  const { currentLanguage, availableLanguages, changeLanguage, isPending } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (code: Locale) => {
    changeLanguage(code);
    setIsOpen(false);
  };

  const currentLangInfo = availableLanguages.find((l) => l.code === currentLanguage);

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={isPending}
        className={cn(
          "inline-flex w-full items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
          isPending && "opacity-70 cursor-wait"
        )}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label={t("language_switcher")}
      >
        <Globe className="h-4 w-4" />
        <span>{currentLangInfo?.nativeName || "English"}</span>
        <ChevronDown className="h-4 w-4 opacity-50" />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 z-50 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none dark:bg-slate-800 dark:ring-slate-700"
          role="menu"
          aria-orientation="vertical"
          tabIndex={-1}
        >
          <div className="py-1 max-h-80 overflow-y-auto" role="none">
            {availableLanguages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleSelect(lang.code)}
                className={cn(
                  "flex w-full items-center justify-between px-4 py-2 text-sm",
                  currentLanguage === lang.code
                    ? "bg-slate-100 text-slate-900 font-semibold dark:bg-slate-700 dark:text-white"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700"
                )}
                role="menuitem"
                tabIndex={-1}
              >
                <span>{lang.nativeName}</span>
                {currentLanguage === lang.code && <Check className="h-4 w-4" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
