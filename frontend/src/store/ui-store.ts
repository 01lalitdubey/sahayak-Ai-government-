/**
 * UI Store — Sahayak AI (Zustand)
 * Manages global UI state: sidebar open/close, loading overlays, toasts.
 * Keeps UI state out of React component trees for cleaner architecture.
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";

interface UIState {
  // ── Sidebar ──────────────────────────────────────────────────────────
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // ── Global loading overlay ────────────────────────────────────────────
  isLoading: boolean;
  setLoading: (loading: boolean) => void;

  // ── Mobile menu ───────────────────────────────────────────────────────
  isMobileMenuOpen: boolean;
  toggleMobileMenu: () => void;
  closeMobileMenu: () => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    (set) => ({
      // Sidebar
      isSidebarOpen: true,
      toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),
      setSidebarOpen: (open) => set({ isSidebarOpen: open }),

      // Loading
      isLoading: false,
      setLoading: (loading) => set({ isLoading: loading }),

      // Mobile menu
      isMobileMenuOpen: false,
      toggleMobileMenu: () => set((s) => ({ isMobileMenuOpen: !s.isMobileMenuOpen })),
      closeMobileMenu: () => set({ isMobileMenuOpen: false }),
    }),
    { name: "UIStore" },
  ),
);
