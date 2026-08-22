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

  // ── Environment variables exposed to the browser ────────────────────────
  // Prefix with NEXT_PUBLIC_ for client-side availability
  env: {
    NEXT_PUBLIC_APP_NAME: process.env["NEXT_PUBLIC_APP_NAME"] ?? "Sahayak AI",
    NEXT_PUBLIC_APP_VERSION: process.env["NEXT_PUBLIC_APP_VERSION"] ?? "0.1.0",
  },

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
