import type { Metadata } from "next";
import { Landmark } from "lucide-react";
import Link from "next/link";
import { GuestRoute } from "@/components/auth/GuestRoute";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { APP_NAME, ROUTES } from "@/lib/constants";

export const metadata: Metadata = { title: "Create Account" };

export default function RegisterPage() {
  return (
    <GuestRoute>
      <div className="min-h-screen flex">
        {/* ── Left branding panel ─────────────────────────────────────── */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary/90 to-primary flex-col items-center justify-center p-12 text-white">
          <div className="max-w-sm text-center space-y-6">
            <Landmark className="h-16 w-16 mx-auto opacity-90" />
            <h1 className="text-3xl font-bold">{APP_NAME}</h1>
            <p className="text-primary-foreground/80 text-lg leading-relaxed">
              Join thousands of citizens who have already discovered
              schemes they qualify for.
            </p>
            <ul className="text-left space-y-3 pt-2">
              {[
                "Personalised scheme recommendations",
                "Eligibility checker in your language",
                "AI-assisted explanations",
                "Completely free",
              ].map((item) => (
                <li key={item} className="flex items-center gap-2 text-sm text-primary-foreground/90">
                  <span className="h-1.5 w-1.5 rounded-full bg-white flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* ── Form panel ──────────────────────────────────────────────── */}
        <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
          <div className="w-full max-w-sm space-y-6">
            <div className="flex items-center gap-2 lg:hidden">
              <Landmark className="h-6 w-6 text-primary" />
              <Link href={ROUTES.HOME} className="font-bold text-xl text-gradient">
                {APP_NAME}
              </Link>
            </div>

            <div>
              <h2 className="text-2xl font-bold tracking-tight">Create your account</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Free forever · No credit card required
              </p>
            </div>

            <RegisterForm />
          </div>
        </div>
      </div>
    </GuestRoute>
  );
}
