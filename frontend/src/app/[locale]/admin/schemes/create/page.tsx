"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { MainLayout } from "@/components/layout/MainLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { SchemeForm } from "@/components/schemes/SchemeForm";
import { Button } from "@/components/ui/button";
import { useCreateScheme } from "@/hooks/use-schemes";
import { showToast } from "@/components/ui/toast-utils";
import type { SchemeCreatePayload } from "@/types/scheme";

function CreateSchemeContent() {
  const router = useRouter();
  const createMut = useCreateScheme();

  async function handleSubmit(data: SchemeCreatePayload) {
    try {
      await createMut.mutateAsync(data);
      showToast(data.is_active ? "Scheme published successfully!" : "Scheme saved as draft successfully!", "success");
      router.push("/admin/schemes");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      showToast(msg ?? "Failed to create scheme.", "error");
      throw err; // keep form in submitting=false state
    }
  }

  return (
    <div className="page-container py-8 max-w-5xl space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" asChild className="-ml-2">
          <Link href="/admin/schemes"><ArrowLeft className="h-4 w-4 mr-1.5" />Back</Link>
        </Button>
      </div>
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Add New Scheme</h1>
        <p className="text-gray-500 mt-2">Follow the steps below to configure a new government scheme. You can save as a draft or publish immediately.</p>
      </div>

      <div className="mt-8">
        <SchemeForm onSubmit={handleSubmit} isEditing={false} />
      </div>
    </div>
  );
}

export default function CreateSchemePage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <MainLayout>
        <CreateSchemeContent />
      </MainLayout>
    </ProtectedRoute>
  );
}
