/**
 * Health Service — Sahayak AI
 * Checks backend connectivity. Used on app load and in a status indicator.
 */

import { apiService } from "@/services/api.service";

interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
}

export const healthService = {
  async check(): Promise<HealthStatus | null> {
    try {
      const res = await apiService.get<HealthStatus>("/health");
      return res.data;
    } catch {
      return null;
    }
  },
};
