/**
 * RAG / Voice Assistant Service — Sahayak AI
 * All HTTP calls to /api/v1/rag/* go through here.
 */

import apiClient from "@/lib/axios";
import { API_BASE_URL } from "@/lib/constants";
import type {
  RagAnswer,
  RagHealth,
  RagLanguagesResponse,
} from "@/types/rag";

const BASE = "/api/v1/rag";

export const ragService = {
  async getLanguages(): Promise<RagLanguagesResponse> {
    const res = await apiClient.get<RagLanguagesResponse>(`${BASE}/languages`);
    return res.data;
  },

  async getHealth(): Promise<RagHealth> {
    const res = await apiClient.get<RagHealth>(`${BASE}/health`);
    return res.data;
  },

  /** Ask a text question. `language` is one of the 13 codes or "auto". */
  async ask(query: string, language: string): Promise<RagAnswer> {
    // The pipeline chains several Groq calls + TTS and can take 30-60s;
    // override the client's default 15s timeout.
    const res = await apiClient.post<RagAnswer>(
      `${BASE}/query`,
      { query, language },
      { timeout: 120_000 },
    );
    return res.data;
  },

  /** Ask a spoken question. `audio` is a recorded Blob (webm/ogg/mp4/wav). */
  async askVoice(audio: Blob, language: string): Promise<RagAnswer> {
    const form = new FormData();
    const ext = (audio.type.split("/")[1] || "webm").split(";")[0];
    form.append("audio", audio, `question.${ext}`);
    form.append("language", language);
    const res = await apiClient.post<RagAnswer>(`${BASE}/voice`, form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120_000,
    });
    return res.data;
  },

  /** Absolute URL for a generated TTS clip returned as a relative path. */
  audioUrl(relativePath: string): string {
    if (/^https?:\/\//.test(relativePath)) return relativePath;
    return `${API_BASE_URL}${relativePath}`;
  },
};
