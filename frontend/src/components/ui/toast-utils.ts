/**
 * Simple toast helper — lightweight wrapper so components
 * don't need to import from multiple places.
 * Uses browser alert as fallback (replaced by shadcn Toast in Phase 5+).
 */

type ToastType = "success" | "error" | "info";

export function showToast(message: string, type: ToastType = "info") {
  // In production this will be replaced with a proper toast notification system.
  // For now we use console + a simple DOM event that the ToastContainer listens to.
  if (typeof window !== "undefined") {
    const event = new CustomEvent("sahayak-toast", {
      detail: { message, type },
    });
    window.dispatchEvent(event);
  }
}
