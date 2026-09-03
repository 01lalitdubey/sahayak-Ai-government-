/**
 * RAG / Voice Assistant hooks — Sahayak AI
 */

"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ragService } from "@/services/rag.service";

export const RAG_KEYS = {
  languages: ["rag", "languages"] as const,
  health: ["rag", "health"] as const,
};

export function useRagLanguages() {
  return useQuery({
    queryKey: RAG_KEYS.languages,
    queryFn: () => ragService.getLanguages(),
    staleTime: 1000 * 60 * 60,
  });
}

export function useRagHealth() {
  return useQuery({
    queryKey: RAG_KEYS.health,
    queryFn: () => ragService.getHealth(),
    staleTime: 1000 * 60 * 5,
    retry: false,
  });
}

export function useAskRag() {
  return useMutation({
    mutationFn: ({ query, language }: { query: string; language: string }) =>
      ragService.ask(query, language),
  });
}

export function useAskRagVoice() {
  return useMutation({
    mutationFn: ({ audio, language }: { audio: Blob; language: string }) =>
      ragService.askVoice(audio, language),
  });
}
