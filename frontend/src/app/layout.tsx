import { ReactNode } from "react";

// Since we have a root `not-found.tsx` page, a root layout file is required by Next.js 15
export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
