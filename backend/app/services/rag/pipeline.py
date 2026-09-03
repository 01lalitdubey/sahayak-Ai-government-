"""
RAG pipeline orchestrator — Sahayak AI
======================================
Voice/Text → Whisper → Language Resolution → gpt-oss-20b (query→EN)
→ all-MiniLM-L6-v2 → ChromaDB → deterministic eligibility rules
→ gpt-oss-120b (answer written directly in the resolved language)
→ sources → gTTS
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import RagIndexEmptyException, ValidationException
from app.core.logging import get_logger
from app.models.chat_history import ChatHistory
from app.models.enums import LanguageEnum
from app.services.rag import embeddings, tts, vector_store
from app.services.rag.groq_client import GroqClient
from app.services.rag.languages import (
    SUPPORTED_LANGUAGES,
    answer_in_expected_script,
    detect_text_language,
    resolve_language,
)

logger = get_logger(__name__)

# Whisper (Groq large-v3) accepts these as a `language` hint. Odia ('or') is the
# only one of our 13 it rejects → we omit the hint and let ASR auto-detect,
# while resolve_language() still forces the answer/TTS language.
WHISPER_HINTABLE: frozenset[str] = frozenset(
    {"en", "hi", "ur", "bn", "as", "ta", "te", "mr", "gu", "kn", "ml", "pa"}
)


def _answer_system(target_english_name: str, target_native_name: str) -> str:
    return (
        "You are Sahayak AI, an assistant that explains Indian government welfare "
        "schemes to ordinary citizens. Answer ONLY using the CONTEXT below. "
        "If the context does not contain the answer, say you do not have that "
        "information and suggest checking the official scheme website. "
        "Never invent scheme names, amounts, dates, or eligibility rules. "
        "When the context includes an ELIGIBILITY line for the user, reflect it "
        "honestly. Keep the answer short, concrete and easy to read aloud. "
        f"Write the ENTIRE answer in {target_english_name} ({target_native_name}) "
        "using that language's OWN NATIVE SCRIPT — every sentence, heading and "
        "list label. Do NOT romanise or transliterate into Latin letters, and do "
        "NOT add an English translation. The only Latin characters allowed are "
        "inside URLs, phone numbers, digits and untranslatable proper nouns. "
        "Use simple wording a rural reader understands. Keep scheme names, "
        "amounts, URLs and phone numbers as-is."
    )


@dataclass
class RagSource:
    scheme_id: str
    scheme_code: str
    scheme_name: str
    official_url: str
    official_pdf_url: str
    similarity: float
    eligibility_status: Optional[str] = None


@dataclass
class RagResult:
    answer: str
    answer_language: str
    language_source: str          # selected | asr | detected | fallback
    detected_language: Optional[str]
    query_language: str
    transcript: Optional[str]
    used_query: str
    english_query: str
    sources: list[RagSource] = field(default_factory=list)
    audio_url: Optional[str] = None
    tts_available: bool = False
    grounded: bool = True

    def to_dict(self) -> dict[str, Any]:
        spec = SUPPORTED_LANGUAGES.get(self.answer_language)
        return {
            "answer": self.answer,
            "answer_language": self.answer_language,
            "answer_language_name": spec.english_name if spec else self.answer_language,
            "answer_language_native": spec.native_name if spec else self.answer_language,
            "language_source": self.language_source,
            "detected_language": self.detected_language,
            "query_language": self.query_language,
            "transcript": self.transcript,
            "used_query": self.used_query,
            "english_query": self.english_query,
            "grounded": self.grounded,
            "tts_available": self.tts_available,
            "audio_url": self.audio_url,
            "sources": [
                {
                    "scheme_id": s.scheme_id,
                    "scheme_code": s.scheme_code,
                    "scheme_name": s.scheme_name,
                    "official_url": s.official_url or None,
                    "official_pdf_url": s.official_pdf_url or None,
                    "similarity": s.similarity,
                    "eligibility_status": s.eligibility_status,
                }
                for s in self.sources
            ],
        }


class RagPipeline:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._groq = GroqClient()  # raises RagDisabledException if no key

    # ── public entry point ───────────────────────────────────────────────
    async def run(
        self,
        *,
        query_text: Optional[str] = None,
        audio: Optional[bytes] = None,
        audio_filename: str = "audio.webm",
        requested_language: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> RagResult:
        transcript: Optional[str] = None
        asr_detected: Optional[str] = None

        # 1. ASR ---------------------------------------------------------------
        if audio:
            if not settings.RAG_ENABLE_ASR:
                raise ValidationException("Voice input is disabled on this server.")
            whisper_hint = None
            req_norm = (requested_language or "").strip().lower()
            if (
                req_norm
                and req_norm != "auto"
                and req_norm in SUPPORTED_LANGUAGES
                and SUPPORTED_LANGUAGES[req_norm].whisper_code in WHISPER_HINTABLE
            ):
                whisper_hint = SUPPORTED_LANGUAGES[req_norm].whisper_code
            # Whisper large-v3 has no Odia hint — omit it and let ASR auto-detect;
            # the answer + TTS language is still forced by resolve_language().
            transcript, asr_detected = await self._groq.transcribe(
                audio, audio_filename, language=whisper_hint
            )
            query_text = transcript

        # 2. validate query --------------------------------------------------
        used_query = (query_text or "").strip()
        if not used_query:
            raise ValidationException("Empty query. Provide text or speech.")
        if len(used_query) > settings.RAG_MAX_QUERY_CHARS:
            used_query = used_query[: settings.RAG_MAX_QUERY_CHARS]

        # 3. language resolution ------------------------------------------------
        answer_language, language_source = resolve_language(
            requested=requested_language,
            asr_detected=asr_detected,
            text=used_query,
        )
        answer_spec = SUPPORTED_LANGUAGES[answer_language]

        # language the QUESTION is written in (independent of the answer lang)
        query_language = detect_text_language(used_query)
        query_spec = SUPPORTED_LANGUAGES.get(query_language, SUPPORTED_LANGUAGES["en"])

        # 4. translate query → English for retrieval (GROQ_TRANSLATION_MODEL) --
        if query_language == "en":
            english_query = used_query
        else:
            english_query = await self._groq.translate(
                used_query, source_name=query_spec.english_name, target_name="English"
            ) or used_query

        # 5. embed + 6. retrieve ------------------------------------------------
        col_size = vector_store.count()
        if col_size == 0:
            raise RagIndexEmptyException()
        qvec = await embeddings.embed_one(english_query)
        chunks = vector_store.query(qvec, top_k=settings.RAG_TOP_K)
        if settings.RAG_MIN_SCORE > 0:
            chunks = [c for c in chunks if c.similarity >= settings.RAG_MIN_SCORE]

        # 7. deterministic eligibility rules ---------------------------------
        elig_by_scheme: dict[str, str] = {}
        if user_id and chunks:
            elig_by_scheme = await self._evaluate_eligibility(
                user_id, [c.scheme_id for c in chunks]
            )

        # 8. build grounded context -------------------------------------------
        grounded = bool(chunks)
        context_blocks: list[str] = []
        sources: list[RagSource] = []
        for c in chunks:
            block = [f"[{c.scheme_name} — code {c.scheme_code}]", c.text]
            status = elig_by_scheme.get(c.scheme_id)
            if status:
                block.append(f"ELIGIBILITY for this user (deterministic rules): {status}")
            url = c.metadata.get("official_url") or ""
            if url:
                block.append(f"Official website: {url}")
            context_blocks.append("\n".join(block))
            sources.append(
                RagSource(
                    scheme_id=c.scheme_id,
                    scheme_code=c.scheme_code,
                    scheme_name=c.scheme_name,
                    official_url=str(c.metadata.get("official_url") or ""),
                    official_pdf_url=str(c.metadata.get("official_pdf_url") or ""),
                    similarity=c.similarity,
                    eligibility_status=status,
                )
            )

        context = "\n\n---\n\n".join(context_blocks) if context_blocks else "(no matching schemes)"

        # 9. answer — generated DIRECTLY in the resolved language (gpt-oss-120b)
        system = _answer_system(answer_spec.english_name, answer_spec.native_name)
        user_prompt = (
            f"USER QUESTION: {used_query}\n"
            f"(English rendering for reference: {english_query})\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"Answer the question now in {answer_spec.english_name}, using only the "
            "context above."
        )
        answer_final = await self._groq.answer(system, user_prompt)

        # Script guard: some models (e.g. gpt-oss on Marathi) romanise the answer.
        # A romanised answer would make target-language TTS speak the wrong
        # language, so retry once, hard, then translate as a last resort.
        if answer_final and answer_language != "en" and not answer_in_expected_script(
            answer_final, answer_language
        ):
            logger.warning(
                "Answer for '%s' came back in the wrong script — correcting.",
                answer_language,
            )
            fix_system = (
                f"Rewrite the text ENTIRELY in {answer_spec.english_name} "
                f"({answer_spec.native_name}) using its native script only. "
                "Do not romanise. Do not add anything. Keep URLs, digits and "
                "phone numbers as they are."
            )
            retry = await self._groq.answer(fix_system, answer_final)
            if retry and answer_in_expected_script(retry, answer_language):
                answer_final = retry
            else:
                translated = await self._groq.translate(
                    answer_final,
                    source_name=f"{answer_spec.english_name} (romanised)",
                    target_name=f"{answer_spec.english_name} in its native script",
                )
                if translated and answer_in_expected_script(translated, answer_language):
                    answer_final = translated

        if not answer_final:
            answer_final = (
                "I could not generate an answer right now. Please try rephrasing "
                "your question or check the official scheme website."
            )

        # 11. TTS in the resolved language ----------------------------------
        audio_name = await tts.synthesize(answer_final, answer_language)
        audio_url = f"/api/v1/rag/audio/{audio_name}" if audio_name else None

        result = RagResult(
            answer=answer_final,
            answer_language=answer_language,
            language_source=language_source,
            detected_language=asr_detected or (query_language if language_source == "detected" else None),
            query_language=query_language,
            transcript=transcript,
            used_query=used_query,
            english_query=english_query,
            sources=sources,
            audio_url=audio_url,
            tts_available=tts.tts_supported(answer_language),
            grounded=grounded,
        )

        await self._log_history(user_id, used_query, answer_final, answer_language)
        return result

    # ── helpers ─────────────────────────────────────────────────────────
    async def _evaluate_eligibility(
        self, user_id: uuid.UUID, scheme_ids: list[str]
    ) -> dict[str, str]:
        from app.core.exceptions import ProfileIncompleteException
        from app.services.eligibility_service import EligibilityService

        svc = EligibilityService(self._db)
        out: dict[str, str] = {}
        seen: set[str] = set()
        for sid in scheme_ids:
            if not sid or sid in seen:
                continue
            seen.add(sid)
            try:
                res = await svc.evaluate_scheme(uuid.UUID(sid), user_id)
            except ProfileIncompleteException:
                return {}  # no profile → skip eligibility entirely
            except Exception as exc:  # noqa: BLE001
                logger.warning("eligibility eval failed for %s: %s", sid, exc)
                continue
            label = {
                "eligible": "Likely ELIGIBLE — all recorded rules pass.",
                "not_eligible": "Likely NOT eligible — one or more rules fail.",
                "incomplete_profile": "Cannot confirm — user profile is missing some fields.",
                "no_rules": "No eligibility restrictions recorded for this scheme.",
            }.get(res.status, res.status)
            if res.status in ("not_eligible", "incomplete_profile") and res.failed_rules:
                reasons = "; ".join(r.reason for r in res.failed_rules[:3])
                label += f" Reasons: {reasons}"
            out[sid] = label
        return out

    async def _log_history(
        self,
        user_id: Optional[uuid.UUID],
        question: str,
        answer: str,
        lang: str,
    ) -> None:
        if not user_id:
            return
        try:
            lang_enum = LanguageEnum(lang)
        except ValueError:
            lang_enum = LanguageEnum.ENGLISH
        # Wrap in a SAVEPOINT so a logging failure can never poison the request's
        # session / outer commit — the answer must always be returned.
        try:
            async with self._db.begin_nested():
                self._db.add(
                    ChatHistory(
                        user_id=user_id,
                        question=question[:8000],
                        answer=answer[:8000],
                        language=lang_enum,
                    )
                )
        except Exception as exc:  # noqa: BLE001 - logging must never break the answer
            logger.warning("chat_history write skipped: %s", exc)
