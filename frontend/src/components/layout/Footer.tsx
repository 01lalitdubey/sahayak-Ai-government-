/**
 * Footer — Sahayak AI
 * Site-wide footer with links, branding, and attribution.
 */

import Link from "next/link";
import { Landmark } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { APP_NAME, APP_VERSION, ROUTES } from "@/lib/constants";
import { useTranslations } from "next-intl";

const FOOTER_LINKS = {
  product: [
    { key: "dashboard", href: ROUTES.DASHBOARD },
    { key: "schemes", href: ROUTES.SCHEMES },
    { key: "eligibility_check", href: ROUTES.ELIGIBILITY },
    { key: "ai_chat", href: ROUTES.CHAT },
  ],
  account: [
    { key: "sign_in", href: ROUTES.LOGIN },
    { key: "register", href: ROUTES.REGISTER },
    { key: "profile", href: ROUTES.PROFILE },
  ],
  legal: [
    { key: "privacy", href: "#" },
    { key: "terms", href: "#" },
    { key: "disclaimer", href: "#" },
  ],
};

export function Footer() {
  const t = useTranslations("footer");

  return (
    <footer className="border-t bg-background">
      <div className="page-container py-12">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {/* ── Brand column ──────────────────────────────────────────── */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 font-bold text-lg">
              <Landmark className="h-5 w-5 text-primary" aria-hidden="true" />
              <span className="text-gradient">{APP_NAME}</span>
            </Link>
            <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
              {t("description")}
            </p>
            <p className="mt-3 text-xs text-muted-foreground">
              🇮🇳 Made for Bharat
            </p>
          </div>

          {/* ── Link columns ──────────────────────────────────────────── */}
          {Object.entries(FOOTER_LINKS).map(([category, links]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold">{t(category as Parameters<typeof t>[0])}</h3>
              <ul className="mt-3 space-y-2" role="list">
                {links.map((link) => (
                  <li key={link.key}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {t(link.key as Parameters<typeof t>[0])}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <Separator className="my-8" />

        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} {APP_NAME}. {t("all_rights_reserved")}
          </p>
          <p className="text-xs text-muted-foreground">
            v{APP_VERSION} · Built with Next.js 15 & FastAPI
          </p>
        </div>
      </div>
    </footer>
  );
}
