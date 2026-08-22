"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Eye, EyeOff, Loader2, LogIn } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth-store";
import { ROUTES } from "@/lib/constants";

// Schema is now inside the component to use translations

type LoginFormData = {
  email: string;
  password: string;
  rememberMe?: boolean;
};

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const { login } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") ?? ROUTES.DASHBOARD;
  const sessionExpired = searchParams.get("session") === "expired";
  
  const t = useTranslations("auth");
  const tVal = useTranslations("validation");
  const tToast = useTranslations("toasts");

  const loginSchema = z.object({
    email: z.string().min(1, "required").email("invalid_email"),
    password: z.string().min(1, "required"),
    rememberMe: z.boolean().optional(),
  });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { rememberMe: false },
  });

  const rememberMe = watch("rememberMe");

  async function onSubmit(data: LoginFormData) {
    setServerError(null);
    try {
      const res = await authService.login({ email: data.email, password: data.password });
      login(res.access_token, res.refresh_token, res.data);
      router.push(redirect);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setServerError(msg ?? tToast("invalid_credentials"));
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="w-full"
    >
      {/* Session expired banner */}
      {sessionExpired && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{t("session_expired")}</AlertDescription>
        </Alert>
      )}

      {/* Server error */}
      {serverError && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{serverError}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {/* Email */}
        <div className="space-y-1.5">
          <Label htmlFor="email">{t("email_label")}</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder={t("email_placeholder")}
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? "email-error" : undefined}
            {...register("email")}
          />
          {errors.email && (
            <p id="email-error" className="text-xs text-destructive">{tVal(errors.email.message as Parameters<typeof tVal>[0])}</p>
          )}
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">{t("password_label")}</Label>
            <Link
              href="#"
              className="text-xs text-muted-foreground hover:text-primary transition-colors"
            >
              {t("forgot_password")}
            </Link>
          </div>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder={t("password_placeholder")}
              className="pr-10"
              aria-invalid={!!errors.password}
              aria-describedby={errors.password ? "password-error" : undefined}
              {...register("password")}
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p id="password-error" className="text-xs text-destructive">{tVal(errors.password.message as Parameters<typeof tVal>[0])}</p>
          )}
        </div>

        {/* Remember me */}
        <div className="flex items-center gap-2">
          <Checkbox
            id="rememberMe"
            checked={rememberMe}
            onCheckedChange={(v) => setValue("rememberMe", !!v)}
          />
          <Label htmlFor="rememberMe" className="font-normal cursor-pointer">
            {t("keep_signed_in")}
          </Label>
        </div>

        {/* Submit */}
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {t("signing_in")}
            </>
          ) : (
            <>
              <LogIn className="mr-2 h-4 w-4" />
              {t("sign_in_button")}
            </>
          )}
        </Button>
      </form>

      <p className="mt-5 text-center text-sm text-muted-foreground">
        {t("no_account")}{" "}
        <Link href={ROUTES.REGISTER} className="font-medium text-primary hover:underline">
          {t("sign_up_button")}
        </Link>
      </p>
    </motion.div>
  );
}
