/**
 * useHealth — Sahayak AI
 * TanStack Query hook that polls the backend health endpoint.
 */

import { useQuery } from "@tanstack/react-query";
import { healthService } from "@/services/health.service";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => healthService.check(),
    staleTime: 1000 * 30, // 30 seconds
    retry: 1,
  });
}
