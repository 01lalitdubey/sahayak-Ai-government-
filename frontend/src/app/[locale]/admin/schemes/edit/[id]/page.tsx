"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { MainLayout } from "@/components/layout/MainLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { SchemeForm } from "@/components/schemes/SchemeForm";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdminScheme, useUpdateScheme } from "@/hooks/use-schemes";
import { showToast } from "@/components/ui/toast-utils";
import type { SchemeCreatePayload } from "@/types/scheme";

function EditSchemeContent({ id }: { id: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const localePrefix = `/${pathname.split("/")[1]}`;
  const { data, isLoading, isError } = useAdminScheme(id);
  const updateMut = useUpdateScheme(id);
  const scheme = data?.data;

  async function handleSubmit(payload: SchemeCreatePayload) {
    // scheme_code is read-only on update
    const { scheme_code, ...updatePayload } = payload;
    void scheme_code; // intentionally excluded
    try {
      await updateMut.mutateAsync(updatePayload);
      const verb = updatePayload.is_active ? "published" : "saved as draft";
      showToast(`Scheme ${verb} successfully!`, "success");
      // Redirect to admin detail page so admin can see translation status
      router.push(`${localePrefix}/admin/schemes/${id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      showToast(msg ?? "Failed to update scheme.", "error");
      throw err;
    }
  }

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" asChild className="-ml-2">
            <Link href={`${localePrefix}/admin/schemes/${id}`}>
              <ArrowLeft className="h-4 w-4 mr-1.5" /> Back
            </Link>
          </Button>
        </div>

        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            {isLoading ? "Loading…" : `Edit: ${scheme?.name ?? "Scheme"}`}
          </h1>
          {scheme && (
            <p className="mt-1 text-sm font-mono text-gray-400">{scheme.scheme_code}</p>
          )}
          <p className="mt-2 text-sm text-gray-500">
            If you modify any translatable content (name, description, benefits), existing translations will be
            automatically marked <strong>Outdated</strong> and re-queued for IndicTrans2.
          </p>
        </div>

        {isError && (
          <p className="text-red-600 font-medium">
            Scheme not found or you do not have permission to edit it.
          </p>
        )}

        {isLoading && (
          <div className="space-y-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!isLoading && scheme && (
          <SchemeForm
            defaultValues={{
              ...scheme,
              // Ensure all optional text fields are properly passed as strings (not null)
              required_documents: scheme.required_documents ?? "",
              application_process: scheme.application_process ?? "",
              short_description: scheme.short_description ?? "",
              full_description: scheme.full_description ?? "",
              benefits: scheme.benefits ?? "",
              ministry: scheme.ministry ?? "",
              department: scheme.department ?? "",
              state: scheme.state ?? "",
              district: scheme.district ?? "",
              official_url: scheme.official_url ?? "",
              official_pdf_url: scheme.official_pdf_url ?? "",
              contact_email: scheme.contact_email ?? "",
              contact_phone: scheme.contact_phone ?? "",
            }}
            onSubmit={handleSubmit}
            isEditing
          />
        )}
      </div>
    </div>
  );
}

export default function EditSchemePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <ProtectedRoute requiredRole="admin">
      <MainLayout>
        <EditSchemeContent id={id} />
      </MainLayout>
    </ProtectedRoute>
  );
}
