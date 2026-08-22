/**
 * MainLayout — Sahayak AI
 * Public-facing layout: Navbar + main content area + Footer.
 * Used by all public pages (home, login, register, schemes, etc.).
 */

import type { ReactNode } from "react";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1" id="main-content">
        {children}
      </main>
      <Footer />
    </div>
  );
}
