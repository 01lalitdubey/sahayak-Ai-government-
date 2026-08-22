"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Eye, EyeOff, Loader2, UserPlus, CheckCircle2 } from "lucide-react";
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
import { cn } from "@/lib/utils";

// Schema moved inside component to use translations
type RegisterFormData = {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  terms: boolean;
};

function PasswordStrengthBar({ password, tVal }: { password: string; tVal: (key: string) => string }) {
  const checks = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[a-z]/.test(password),
    /\d/.test(password),
    /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(password),
  ];
  const score = checks.filter(Boolean).length;

  const colors = ["", "bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-blue-500", "bg-green-500"];
  const labels = ["", tVal("very_weak"), tVal("weak"), tVal("fair"), tVal("good"), tVal("strong")];

  if (!password) return null;

  return (
    <div className="mt-1.5 space-y-1">
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={cn(
              "h-1 flex-1 rounded-full transition-all duration-300",
              i <= score ? colors[score] : "bg-muted",
            )}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">{labels[score]}</p>
    </div>
  );
}

export function RegisterForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const { login } = useAuthStore();
  const router = useRouter();
  const t = useTranslations("auth");
  const tVal = useTranslations("validation");

  const registerSchema = z
    .object({
      full_name: z.string().min(2, "name_length"),
      email: z.string().min(1, "required").email("invalid_email"),
      password: z
        .string()
        .min(8, "password_length")
        .regex(/[A-Z]/, "password_uppercase")
        .regex(/[a-z]/, "password_lowercase")
        .regex(/\d/, "password_number")
        .regex(/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/, "password_special"),
      confirm_password: z.string().min(1, "required"),
      terms: z.boolean().refine((v) => v === true, { message: "must_accept_terms" }),
    })
    .refine((d) => d.password === d.confirm_password, {
      message: "passwords_dont_match",
      path: ["confirm_password"],
    });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { terms: false },
  });

  const password = watch("password") ?? "";
  const terms = watch("terms");

  async function onSubmit(data: RegisterFormData) {
    setServerError(null);
    try {
      const res = await authService.register({
        email: data.email,
        full_name: data.full_name,
        password: data.password,
        confirm_password: data.confirm_password,
      });
      setSuccess(true);
      login(res.access_token, res.refresh_token, res.data);
      setTimeout(() => router.push(ROUTES.DASHBOARD), 1200);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: string } }; code?: string; message?: string };
      if (!axiosErr.response) {
        // Network error — backend not reachable
        setServerError(t("network_error"));
      } else {
        const msg = axiosErr.response?.data?.message;
        setServerError(msg ?? t("registration_failed"));
      }
    }
  }

  if (success) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center gap-3 py-8 text-center"
      >
        <CheckCircle2 className="h-12 w-12 text-green-500" />
        <h3 className="text-lg font-semibold">{t("account_created")}</h3>
        <p className="text-sm text-muted-foreground">{t("redirecting_dashboard")}</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="w-full"
    >
      {serverError && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{serverError}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {/* Full name */}
        <div className="space-y-1.5">
          <Label htmlFor="full_name">{t("name_label")}</Label>
          <Input
            id="full_name"
            autoComplete="name"
            placeholder={t("name_placeholder")}
            aria-invalid={!!errors.full_name}
            {...register("full_name")}
          />
          {errors.full_name && (
            <p className="text-xs text-destructive">{tVal(errors.full_name.message as Parameters<typeof tVal>[0])}</p>
          )}
        </div>

        {/* Email */}
        <div className="space-y-1.5">
          <Label htmlFor="email">{t("email_label")}</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder={t("email_placeholder")}
            aria-invalid={!!errors.email}
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{tVal(errors.email.message as Parameters<typeof tVal>[0])}</p>
          )}
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <Label htmlFor="password">{t("password_label")}</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              placeholder={t("password_placeholder")}
              className="pr-10"
              aria-invalid={!!errors.password}
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
          <PasswordStrengthBar password={password} tVal={tVal} />
          {errors.password && (
            <p className="text-xs text-destructive">{tVal(errors.password.message as Parameters<typeof tVal>[0])}</p>
          )}
        </div>

        {/* Confirm password */}
        <div className="space-y-1.5">
          <Label htmlFor="confirm_password">{t("confirm_password_label")}</Label>
          <div className="relative">
            <Input
              id="confirm_password"
              type={showConfirm ? "text" : "password"}
              autoComplete="new-password"
              placeholder={t("confirm_password_placeholder")}
              className="pr-10"
              aria-invalid={!!errors.confirm_password}
              {...register("confirm_password")}
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              onClick={() => setShowConfirm((v) => !v)}
              aria-label={showConfirm ? "Hide" : "Show"}
            >
              {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirm_password && (
            <p className="text-xs text-destructive">{tVal(errors.confirm_password.message as Parameters<typeof tVal>[0])}</p>
          )}
        </div>

        {/* Terms */}
        <div className="space-y-1">
          <div className="flex items-start gap-2">
            <Checkbox
              id="terms"
              checked={terms}
              onCheckedChange={(v) => setValue("terms", !!v, { shouldValidate: true })}
              className="mt-0.5"
            />
            <Label htmlFor="terms" className="font-normal cursor-pointer leading-relaxed">
              {t("agree_to_terms")}
              <Link href="#" className="text-primary hover:underline">{t("terms_of_service")}</Link>
              {t("and")}
              <Link href="#" className="text-primary hover:underline">{t("privacy_policy")}</Link>
            </Label>
          </div>
          {errors.terms && (
            <p className="text-xs text-destructive">{tVal(errors.terms.message as Parameters<typeof tVal>[0])}</p>
          )}
        </div>

        {/* Submit */}
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />{t("creating_account")}</>
          ) : (
            <><UserPlus className="mr-2 h-4 w-4" />{t("sign_up_button")}</>
          )}
        </Button>
      </form>

      <p className="mt-5 text-center text-sm text-muted-foreground">
        {t("have_account")}{" "}
        <Link href={ROUTES.LOGIN} className="font-medium text-primary hover:underline">
          {t("sign_in_button")}
        </Link>
      </p>
    </motion.div>
  );
}
