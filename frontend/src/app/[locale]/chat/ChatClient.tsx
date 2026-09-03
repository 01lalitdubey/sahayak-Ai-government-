"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Mic, Square, Send, Volume2, ExternalLink, Loader2, Languages } from "lucide-react";

import { ragService } from "@/services/rag.service";
import { API_BASE_URL } from "@/lib/constants";
import {
  useAskRag,
  useAskRagVoice,
  useRagHealth,
  useRagLanguages,
} from "@/hooks/use-rag";
import type { ChatTurn, RagAnswer } from "@/types/rag";

const STATIC_LANGS = [
  { code: "en", native_name: "English" },
  { code: "hi", native_name: "हिन्दी" },
  { code: "ur", native_name: "اردو" },
  { code: "bn", native_name: "বাংলা" },
  { code: "as", native_name: "অসমীয়া" },
  { code: "ta", native_name: "தமிழ்" },
  { code: "te", native_name: "తెలుగు" },
  { code: "mr", native_name: "मराठी" },
  { code: "gu", native_name: "ગુજરાતી" },
  { code: "kn", native_name: "ಕನ್ನಡ" },
  { code: "ml", native_name: "മലയാളം" },
  { code: "pa", native_name: "ਪੰਜਾਬੀ" },
  { code: "or", native_name: "ଓଡ଼ିଆ" },
];

const RTL = new Set(["ur"]);

function uid() {
  return Math.random().toString(36).slice(2);
}

export function ChatClient() {
  const [language, setLanguage] = useState<string>("auto");
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [recording, setRecording] = useState(false);
  const [recError, setRecError] = useState<string | null>(null);

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const { data: langData } = useRagLanguages();
  const { data: health } = useRagHealth();
  const ask = useAskRag();
  const askVoice = useAskRagVoice();

  // Selector stays on "auto" by default: the answer language follows the
  // language the question is written in (so a Telugu question -> Telugu answer),
  // regardless of the site UI locale. The user can still force a language.

  const languages = useMemo(() => {
    const list = langData?.languages?.length
      ? langData.languages.map((l) => ({ code: l.code, native_name: l.native_name }))
      : STATIC_LANGS;
    return list;
  }, [langData]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  const pushAnswer = useCallback((pendingId: string, ans: RagAnswer) => {
    setTurns((t) =>
      t.map((turn) =>
        turn.id === pendingId
          ? {
              ...turn,
              pending: false,
              text: ans.answer,
              language: ans.answer_language,
              answer: ans,
            }
          : turn,
      ),
    );
  }, []);

  const pushError = useCallback((pendingId: string, msg: string) => {
    setTurns((t) =>
      t.map((turn) =>
        turn.id === pendingId ? { ...turn, pending: false, error: true, text: msg } : turn,
      ),
    );
  }, []);

  const errText = (e: unknown) => {
    const err = e as {
      response?: { data?: { message?: string; detail?: string }; status?: number };
      code?: string;
      message?: string;
    };
    if (!err?.response) {
      // No HTTP response → network / CORS / server down
      return `Cannot reach the assistant API at ${API_BASE_URL}. Is the backend running?`;
    }
    const data = err.response.data;
    return (
      data?.message ||
      data?.detail ||
      `Request failed (HTTP ${err.response.status ?? "?"}).`
    );
  };

  const submitText = useCallback(async () => {
    const q = input.trim();
    if (!q || ask.isPending) return;
    setInput("");
    const userId = uid();
    const pendingId = uid();
    setTurns((t) => [
      ...t,
      { id: userId, role: "user", text: q, language },
      { id: pendingId, role: "assistant", text: "", pending: true },
    ]);
    try {
      const ans = await ask.mutateAsync({ query: q, language });
      pushAnswer(pendingId, ans);
    } catch (e) {
      pushError(pendingId, errText(e));
    }
  }, [input, language, ask, pushAnswer, pushError]);

  const startRecording = useCallback(async () => {
    setRecError(null);
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setRecError("Voice recording is not supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : MediaRecorder.isTypeSupported("audio/mp4")
          ? "audio/mp4"
          : "";
      const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      chunksRef.current = [];
      rec.ondataavailable = (ev) => ev.data.size > 0 && chunksRef.current.push(ev.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((tr) => tr.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: mime || "audio/webm" });
        if (blob.size < 800) {
          setRecError("Recording too short.");
          return;
        }
        const pendingId = uid();
        setTurns((t) => [
          ...t,
          { id: uid(), role: "user", text: "🎤 Voice question…", language },
          { id: pendingId, role: "assistant", text: "", pending: true },
        ]);
        try {
          const ans = await askVoice.mutateAsync({ audio: blob, language });
          setTurns((t) =>
            t.map((turn) =>
              turn.text === "🎤 Voice question…" && turn.role === "user"
                ? { ...turn, text: ans.transcript || turn.text }
                : turn,
            ),
          );
          pushAnswer(pendingId, ans);
        } catch (e) {
          pushError(pendingId, errText(e));
        }
      };
      mediaRef.current = rec;
      rec.start();
      setRecording(true);
    } catch {
      setRecError("Microphone permission denied.");
    }
  }, [language, askVoice, pushAnswer, pushError]);

  const stopRecording = useCallback(() => {
    if (mediaRef.current?.state === "recording") mediaRef.current.stop();
  }, []);

  const disabled = health && !health.rag_enabled;
  const emptyIndex = health && health.rag_enabled && health.collection_size === 0;

  return (
    <div className="mx-auto flex h-[calc(100vh-9rem)] max-w-3xl flex-col gap-3 p-4">
      {/* Controls */}
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Sahayak AI Assistant</h1>
        <label className="flex items-center gap-2 text-sm">
          <Languages className="h-4 w-4 text-muted-foreground" />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="rounded-md border bg-background px-2 py-1.5 text-sm"
          >
            <option value="auto">Auto-detect</option>
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.native_name} ({l.code})
              </option>
            ))}
          </select>
        </label>
      </div>

      {disabled && (
        <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          The AI assistant is not configured on the server (missing <code>GROQ_API_KEY</code>).
        </div>
      )}
      {emptyIndex && (
        <div className="rounded-md border border-blue-300 bg-blue-50 p-3 text-sm text-blue-900">
          No schemes have been indexed yet. An administrator must run{" "}
          <code>POST /api/v1/rag/ingest</code>.
        </div>
      )}

      {/* Transcript */}
      <div
        ref={scrollRef}
        className="flex-1 space-y-4 overflow-y-auto rounded-lg border bg-muted/20 p-4"
      >
        {turns.length === 0 && (
          <p className="mt-8 text-center text-sm text-muted-foreground">
            Ask about any government scheme — eligibility, benefits, documents, how to apply.
            Type or use the microphone, in any of 13 languages.
          </p>
        )}
        {turns.map((turn) => (
          <TurnBubble key={turn.id} turn={turn} />
        ))}
      </div>

      {recError && <p className="text-xs text-red-600">{recError}</p>}

      {/* Composer */}
      <div className="flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submitText();
            }
          }}
          rows={2}
          placeholder="Type your question…"
          dir={RTL.has(language) ? "rtl" : "ltr"}
          className="min-h-[44px] flex-1 resize-none rounded-md border bg-background px-3 py-2 text-sm"
          disabled={!!disabled}
        />
        <button
          type="button"
          onClick={recording ? stopRecording : startRecording}
          disabled={!!disabled || ask.isPending || askVoice.isPending}
          className={`flex h-11 w-11 items-center justify-center rounded-md border ${
            recording ? "bg-red-600 text-white" : "bg-background"
          }`}
          aria-label={recording ? "Stop recording" : "Record voice"}
        >
          {recording ? <Square className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
        </button>
        <button
          type="button"
          onClick={submitText}
          disabled={!!disabled || !input.trim() || ask.isPending}
          className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-primary-foreground disabled:opacity-50"
          aria-label="Send"
        >
          {ask.isPending || askVoice.isPending ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </div>
    </div>
  );
}

function TurnBubble({ turn }: { turn: ChatTurn }) {
  const isUser = turn.role === "user";
  const ans = turn.answer;
  const rtl = turn.language ? RTL.has(turn.language) : false;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
          isUser
            ? "bg-primary text-primary-foreground"
            : turn.error
              ? "bg-red-50 text-red-800 border border-red-200"
              : "bg-background border"
        }`}
        dir={rtl ? "rtl" : "ltr"}
      >
        {turn.pending ? (
          <span className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Thinking…
          </span>
        ) : (
          <p className="whitespace-pre-wrap">{turn.text}</p>
        )}

        {ans && !turn.pending && (
          <div className="mt-2 space-y-2">
            <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="rounded bg-muted px-1.5 py-0.5">
                {ans.answer_language_native} · {ans.answer_language}
              </span>
              <span className="rounded bg-muted px-1.5 py-0.5">
                lang via: {ans.language_source}
              </span>
              {ans.detected_language && (
                <span className="rounded bg-muted px-1.5 py-0.5">
                  detected: {ans.detected_language}
                </span>
              )}
              {!ans.grounded && (
                <span className="rounded bg-amber-100 px-1.5 py-0.5 text-amber-800">
                  no matching scheme
                </span>
              )}
            </div>

            {ans.audio_url && (
              <audio
                controls
                src={ragService.audioUrl(ans.audio_url)}
                className="h-9 w-full"
              >
                <track kind="captions" />
              </audio>
            )}
            {!ans.audio_url && (
              <p className="text-[11px] text-muted-foreground">
                <Volume2 className="mr-1 inline h-3 w-3" />
                {ans.tts_available
                  ? "Audio could not be generated this time — please retry."
                  : "Audio not available for this language."}
              </p>
            )}

            {ans.sources.length > 0 && (
              <details className="rounded-md border bg-muted/30 p-2 text-xs">
                <summary className="cursor-pointer font-medium">
                  Sources ({ans.sources.length})
                </summary>
                <ul className="mt-2 space-y-2">
                  {ans.sources.map((s) => (
                    <li key={s.scheme_id} className="border-t pt-2 first:border-t-0 first:pt-0">
                      <div className="font-medium">{s.scheme_name}</div>
                      <div className="text-muted-foreground">
                        {s.scheme_code} · match {(s.similarity * 100).toFixed(0)}%
                      </div>
                      {s.eligibility_status && (
                        <div className="mt-0.5 text-[11px]">{s.eligibility_status}</div>
                      )}
                      <div className="mt-0.5 flex gap-3">
                        {s.official_url && (
                          <a
                            href={s.official_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline"
                          >
                            Website <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                        {s.official_pdf_url && (
                          <a
                            href={s.official_pdf_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline"
                          >
                            Guidelines PDF <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
