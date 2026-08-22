import type { Metadata } from "next";
import { Suspense } from "react";
import { Landmark } from "lucide-react";
import Link from "next/link";
import { GuestRoute } from "@/components/auth/GuestRoute";
import { LoginForm } from "@/components/auth/LoginForm";
import { APP_NAME, ROUTES } from "@/lib/constants";

export const metadata: Metadata = { title: "Sign In" };

export default function LoginPage() {
  return (
    <GuestRoute>
      <div className="min-h-screen flex">
        {/* ── Left panel — branding (hidden on mobile) ────────────────── */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary/90 to-primary flex-col items-center justify-center p-12 text-white">
          <div className="max-w-sm text-center space-y-6">
            <Landmark className="h-16 w-16 mx-auto opacity-90" />
            <h1 className="text-3xl font-bold">{APP_NAME}</h1>
            <p className="text-primary-foreground/80 text-lg leading-relaxed">
              Your guide to government schemes, subsidies, and benefits —
              in your language.
            </p>
            <div className="pt-4 grid grid-cols-3 gap-4 text-center">
              {["500+ Schemes", "13 Languages", "Free Forever"].map((t) => (
                <div key={t} className="rounded-xl bg-white/10 px-3 py-3">
                  <p className="text-sm font-medium">{t}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Right panel — form ──────────────────────────────────────── */}
        <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
          <div className="w-full max-w-sm space-y-6">
            {/* Mobile brand */}
            <div className="flex items-center gap-2 lg:hidden">
              <Landmark className="h-6 w-6 text-primary" />
              <Link href={ROUTES.HOME} className="font-bold text-xl text-gradient">
                {APP_NAME}
              </Link>
            </div>

            <div>
              <h2 className="text-2xl font-bold tracking-tight">Welcome back</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Sign in to your account to continue
              </p>
            </div>

            <Suspense>
              <LoginForm />
            </Suspense>
          </div>
        </div>
      </div>
    </GuestRoute>
  );
}
