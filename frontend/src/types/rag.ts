/**
 * RAG / Voice Assistant types — Sahayak AI
 * Mirrors app/schemas/rag.py on the backend.
 */

export interface RagSource {
  scheme_id: string;
  scheme_code: string;
  scheme_name: string;
  official_url: string | null;
  official_pdf_url: string | null;
  similarity: number;
  eligibility_status: string | null;
}

export interface RagAnswer {
  answer: string;
  answer_language: string;
  answer_language_name: string;
  answer_language_native: string;
  language_source: "selected" | "asr" | "detected" | "fallback";
  detected_language: string | null;
  query_language: string;
  transcript: string | null;
  used_query: string;
  english_query: string;
  grounded: boolean;
  tts_available: boolean;
  audio_url: string | null;
  sources: RagSource[];
}

export interface RagLanguage {
  code: string;
  english_name: string;
  native_name: string;
  script: string;
  tts_available: boolean;
  tts_engine?: "gtts+mms" | "gtts" | "mms" | "none";
}

export interface RagLanguagesResponse {
  auto_supported: boolean;
  languages: RagLanguage[];
}

export interface RagHealth {
  rag_enabled: boolean;
  asr_enabled: boolean;
  tts_enabled: boolean;
  tts_provider?: string;
  tts_languages?: number;
  embedding_model: string;
  embedding_dim: number | null;
  vector_store_path: string;
  collection: string;
  collection_size: number;
  answer_model: string;
  translation_model: string;
  whisper_model: string;
  languages: number;
}

/** UI-only: one turn in the chat transcript */
export interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  text: string;
  language?: string;
  pending?: boolean;
  error?: boolean;
  answer?: RagAnswer;
}
