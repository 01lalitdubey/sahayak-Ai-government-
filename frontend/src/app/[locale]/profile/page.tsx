"use client";

import { motion } from "framer-motion";
import { User, Mail, Shield, Calendar, CheckCircle2, XCircle } from "lucide-react";
import { MainLayout } from "@/components/layout/MainLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/use-auth";
import { formatDate, capitalize } from "@/lib/utils";
import { useTranslations } from "next-intl";

const ROLE_COLOURS: Record<string, string> = {
  admin: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  super_admin: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  user: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
};

function ProfileSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-64" />
      <div className="grid gap-4 sm:grid-cols-2 mt-6">
        {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
      </div>
    </div>
  );
}

function ProfileContent() {
  const { user, isLoading } = useAuth();
  const t = useTranslations("profile");

  if (isLoading || !user) return <ProfileSkeleton />;

  const fields = [
    { icon: User, label: t("full_name"), value: user.full_name },
    { icon: Mail, label: t("email"), value: user.email },
    {
      icon: Shield,
      label: t("role"),
      value: (
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${ROLE_COLOURS[user.role] ?? ROLE_COLOURS.user}`}>
          {t(user.role as Parameters<typeof t>[0]) || capitalize(user.role.replace("_", " "))}
        </span>
      ),
    },
    {
      icon: Calendar,
      label: t("member_since"),
      value: formatDate(user.created_at),
    },
    {
      icon: user.is_active ? CheckCircle2 : XCircle,
      label: t("account_status"),
      value: (
        <Badge variant={user.is_active ? "default" : "destructive"}>
          {user.is_active ? t("active") : t("inactive")}
        </Badge>
      ),
    },
    {
      icon: user.is_verified ? CheckCircle2 : XCircle,
      label: t("email_verified"),
      value: (
        <Badge variant={user.is_verified ? "default" : "secondary"}>
          {user.is_verified ? t("verified") : t("pending_verification")}
        </Badge>
      ),
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-2xl">
          {user.full_name.charAt(0).toUpperCase()}
        </div>
        <div>
          <h1 className="text-2xl font-bold">{user.full_name}</h1>
          <p className="text-sm text-muted-foreground">{user.email}</p>
        </div>
      </div>

      {/* Detail cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        {fields.map(({ icon: Icon, label, value }) => (
          <Card key={label}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Icon className="h-4 w-4" aria-hidden="true" />
                {label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm font-medium">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <MainLayout>
        <section className="page-container section-padding">
          <ProfileContent />
        </section>
      </MainLayout>
    </ProtectedRoute>
  );
}
