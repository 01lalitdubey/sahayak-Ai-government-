"""
Groq client — Sahayak AI RAG
=============================
Thin async wrapper over Groq's OpenAI-compatible REST API.
One API key drives three models (all overridable via settings):
  * whisper-large-v3    → speech-to-text (+ spoken-language detection)
  * openai/gpt-oss-20b  → query → English translation (for retrieval)
  * openai/gpt-oss-120b → grounded answer, written directly in the target language

Uses httpx directly (already a project dependency) — no extra SDK.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx

from app.core.config import settings
from app.core.exceptions import RagDisabledException, RagServiceException
from app.core.logging import get_logger

logger = get_logger(__name__)

_MAX_RETRIES = 2


class GroqClient:
    def __init__(self) -> None:
        if not settings.rag_enabled:
            raise RagDisabledException()
        self._key = settings.GROQ_API_KEY.strip()
        self._base = settings.GROQ_BASE_URL.rstrip("/")
        self._timeout = settings.RAG_REQUEST_TIMEOUT

    # ── low-level ─────────────────────────────────────────────────────────
    async def _post(self, path: str, *, json: dict | None = None,
                    data: dict | None = None, files: dict | None = None) -> dict:
        url = f"{self._base}{path}"
        headers = {"Authorization": f"Bearer {self._key}"}
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        url, headers=headers, json=json, data=data, files=files
                    )
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise RagServiceException(
                        f"Groq returned {resp.status_code}: {resp.text[:200]}"
                    )
                if resp.status_code >= 400:
                    # 4xx (bad request / auth) — do not retry
                    logger.error("Groq %s -> %s: %s", path, resp.status_code, resp.text[:300])
                    raise RagServiceException(
                        f"Groq rejected the request ({resp.status_code})."
                    )
                return resp.json()
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                logger.warning("Groq %s network error (attempt %d): %s", path, attempt + 1, exc)
            except RagServiceException as exc:
                last_exc = exc
                if "rejected the request" in str(exc):
                    raise
                logger.warning("Groq %s retryable error (attempt %d): %s", path, attempt + 1, exc)
            await asyncio.sleep(0.8 * (attempt + 1))
        raise RagServiceException(f"Groq unreachable after retries: {last_exc}")

    # ── ASR ──────────────────────────────────────────────────────────────
    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        *,
        language: Optional[str] = None,
    ) -> tuple[str, Optional[str]]:
        """
        Returns (transcript_text, detected_language_code_or_None).
        Pass `language` (Whisper code) to bias/force recognition when the user
        has selected a concrete language; omit it for auto-detect.
        """
        data: dict[str, str] = {
            "model": settings.GROQ_WHISPER_MODEL,
            "response_format": "verbose_json",
            "temperature": "0",
        }
        if language:
            data["language"] = language
        files = {"file": (filename, audio_bytes, "application/octet-stream")}
        payload = await self._post("/audio/transcriptions", data=data, files=files)
        text = (payload.get("text") or "").strip()
        detected = payload.get("language")  # verbose_json includes this
        if isinstance(detected, str):
            detected = detected.strip().lower() or None
        return text, detected

    # ── Chat completion ──────────────────────────────────────────────────
    async def _chat(self, model: str, system: str, user: str,
                    *, temperature: float = 0.2, max_tokens: int = 1024) -> str:
        payload = await self._post(
            "/chat/completions",
            json={
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        try:
            return (payload["choices"][0]["message"]["content"] or "").strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RagServiceException(f"Malformed Groq response: {exc}")

    # ── Translation (GROQ_TRANSLATION_MODEL) ─────────────────────────────
    async def translate(self, text: str, *, source_name: str, target_name: str) -> str:
        """Translate `text` from source_name → target_name. No-op if names match."""
        if not text or not text.strip():
            return ""
        if source_name.lower() == target_name.lower():
            return text.strip()
        system = (
            "You are a professional translator for Indian government-scheme "
            "content. Translate the user's message from "
            f"{source_name} into {target_name}. Output ONLY the translation — "
            "no preamble, no notes, no quotes. Preserve numbers, dates, scheme "
            "names, URLs and phone numbers exactly. Keep the meaning precise and "
            "the tone simple enough for a rural reader."
        )
        out = await self._chat(
            settings.GROQ_TRANSLATION_MODEL, system, text,
            temperature=0.0, max_tokens=1400,
        )
        return out or text

    # ── Answer generation (gpt-oss-120b) ────────────────────────────────
    async def answer(self, system: str, user: str) -> str:
        return await self._chat(
            settings.GROQ_ANSWER_MODEL, system, user,
            temperature=0.15, max_tokens=900,
        )
