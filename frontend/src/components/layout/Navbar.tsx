"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Menu,
  X,
  Sun,
  Moon,
  Landmark,
  LogOut,
  User,
  LayoutDashboard,
  Shield,
  BookOpen,
  Sparkles,
} from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/store/ui-store";
import { useAuth } from "@/hooks/use-auth";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { LanguageSwitcher } from "@/components/language/LanguageSwitcher";
import { useTranslations } from "next-intl";

const NAV_LINKS = [
  { key: "schemes", href: ROUTES.SCHEMES },
  { key: "eligibility", href: ROUTES.ELIGIBILITY },
  { key: "chat", href: ROUTES.CHAT },
];

export function Navbar() {
  const { isMobileMenuOpen, toggleMobileMenu, closeMobileMenu } = useUIStore();
  const { theme, setTheme } = useTheme();
  const { isAuthenticated, user, isAdmin, logout } = useAuth();
  const router = useRouter();
  const t = useTranslations("navbar");
  const tUi = useTranslations("ui");

  async function handleLogout() {
    closeMobileMenu();
    await logout();
    router.push(ROUTES.LOGIN);
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="page-container flex h-16 items-center justify-between">
        {/* Brand */}
        <Link
          href={isAuthenticated ? ROUTES.DASHBOARD : ROUTES.HOME}
          className="flex items-center gap-2 font-bold text-xl"
          onClick={closeMobileMenu}
        >
          <Landmark className="h-6 w-6 text-primary" aria-hidden="true" />
          <span className="text-gradient">{t("brand")}</span>
        </Link>

        {/* Desktop nav */}
        <ul className="hidden md:flex items-center gap-1" role="list">
          {isAuthenticated && (
            <li>
              <Link
                href={ROUTES.DASHBOARD}
                className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground flex items-center gap-1.5"
              >
                <LayoutDashboard className="h-3.5 w-3.5" />
                {t("dashboard")}
              </Link>
            </li>
          )}
          {isAuthenticated && (
            <li>
              <Link
                href={ROUTES.RECOMMENDATIONS}
                className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground flex items-center gap-1.5"
              >
                <Sparkles className="h-3.5 w-3.5" />
                {t("recommendations")}
              </Link>
            </li>
          )}
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                {t(link.key as Parameters<typeof t>[0])}
              </Link>
            </li>
          ))}
          {isAuthenticated && isAdmin && (
            <li>
              <Link
                href={ROUTES.ADMIN_SCHEMES}
                className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground flex items-center gap-1.5"
              >
                <BookOpen className="h-3.5 w-3.5" />
                {t("manage_schemes")}
              </Link>
            </li>
          )}
          {isAuthenticated && isAdmin && (
            <li>
              <Link
                href={ROUTES.ADMIN}
                className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground flex items-center gap-1.5"
              >
                <Shield className="h-3.5 w-3.5" />
                {t("admin")}
              </Link>
            </li>
          )}
        </ul>

        {/* Right controls */}
        <div className="flex items-center gap-2">
          <LanguageSwitcher />

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label={tUi("toggle_theme")}
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>

          {isAuthenticated ? (
            <div className="hidden md:flex items-center gap-2">
              <Link
                href={ROUTES.PROFILE}
                className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium hover:bg-accent transition-colors"
              >
                <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                  {user?.full_name?.charAt(0).toUpperCase()}
                </div>
                <span className="text-muted-foreground">
                  {user?.full_name?.split(" ")[0]}
                </span>
              </Link>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-muted-foreground hover:text-destructive"
              >
                <LogOut className="h-4 w-4 mr-1.5" />
                {t("logout")}
              </Button>
            </div>
          ) : (
            <div className="hidden md:flex items-center gap-2">
              <Button variant="ghost" size="sm" asChild>
                <Link href={ROUTES.LOGIN}>{t("login")}</Link>
              </Button>
              <Button size="sm" asChild>
                <Link href={ROUTES.REGISTER}>{t("register")}</Link>
              </Button>
            </div>
          )}

          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={toggleMobileMenu}
            aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>
      </nav>

      {/* Mobile drawer */}
      <div
        className={cn(
          "md:hidden border-t bg-background transition-all duration-300",
          isMobileMenuOpen
            ? "max-h-screen opacity-100"
            : "max-h-0 overflow-hidden opacity-0",
        )}
      >
        <ul className="page-container flex flex-col gap-1 py-4" role="list">
          {isAuthenticated && (
            <li>
              <Link
                href={ROUTES.DASHBOARD}
                className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                onClick={closeMobileMenu}
              >
                <LayoutDashboard className="h-4 w-4" />
                {t("dashboard")}
              </Link>
            </li>
          )}
          {isAuthenticated && (
            <li>
              <Link
                href={ROUTES.RECOMMENDATIONS}
                className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                onClick={closeMobileMenu}
              >
                <Sparkles className="h-4 w-4" />
                {t("recommendations")}
              </Link>
            </li>
          )}
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="block rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                onClick={closeMobileMenu}
              >
                {t(link.key as Parameters<typeof t>[0])}
              </Link>
            </li>
          ))}
          {isAuthenticated && isAdmin && (
            <li>
              <Link
                href={ROUTES.ADMIN_SCHEMES}
                className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent"
                onClick={closeMobileMenu}
              >
                <BookOpen className="h-4 w-4" />
                {t("manage_schemes")}
              </Link>
            </li>
          )}
          {isAuthenticated && isAdmin && (
            <li>
              <Link
                href={ROUTES.ADMIN}
                className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent"
                onClick={closeMobileMenu}
              >
                <Shield className="h-4 w-4" />
                {t("admin")}
              </Link>
            </li>
          )}
          <li className="pt-2 border-t mt-2">
            {isAuthenticated ? (
              <div className="space-y-1">
                <Link
                  href={ROUTES.PROFILE}
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent"
                  onClick={closeMobileMenu}
                >
                  <User className="h-4 w-4" />
                  {t("profile")}
                </Link>
                <button
                  className="w-full flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-destructive hover:bg-destructive/10"
                  onClick={handleLogout}
                >
                  <LogOut className="h-4 w-4" />
                  {t("logout")}
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1" asChild>
                  <Link href={ROUTES.LOGIN} onClick={closeMobileMenu}>
                    {t("login")}
                  </Link>
                </Button>
                <Button size="sm" className="flex-1" asChild>
                  <Link href={ROUTES.REGISTER} onClick={closeMobileMenu}>
                    {t("register")}
                  </Link>
                </Button>
              </div>
            )}
          </li>
        </ul>
      </div>
    </header>
  );
}
