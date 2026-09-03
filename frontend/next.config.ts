import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const nextConfig: NextConfig = {
  // ── Strict React mode for catching subtle bugs ─────────────────────────
  reactStrictMode: true,

  // ── Image optimization domains (add CDN / S3 bucket later) ────────────
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.gov.in",
      },
    ],
  },

  // NEXT_PUBLIC_-prefixed vars are exposed to the browser automatically;
  // defaults live at the point of use in src/lib/constants.ts.

  // ── Redirect / Rewrite rules ─────────────────────────────────────────────
  async redirects() {
    return [
      {
        source: "/home",
        destination: "/dashboard",
        permanent: true,
      },
    ];
  },
};

const withNextIntl = createNextIntlPlugin();

export default withNextIntl(nextConfig);
