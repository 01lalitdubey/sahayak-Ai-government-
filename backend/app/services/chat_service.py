"""
Chat Service — Sahayak AI
============================
RAG-style conversational assistant over the schemes catalogue.

Pipeline:
  1. Detect the user's language and translate their message to English (Groq).
  2. Search the schemes table (SchemeRepository.search) using the English text.
  3. Generate an answer in English from that context (Groq) — generation always
     happens in English regardless of the query's or context's language, because
     the model tends to mirror the retrieved context's language over an explicit
     "reply in X" instruction when the two conflict (schemes data is a mix of
     languages). Localizing afterwards, a plain translation task, is reliable.
  4. Localize the answer into the detected language (Groq), unless it's English.
  5. Persist the turn to chat_history via ChatRepository.

`reasoning_effort="low"` plus a generous `max_completion_tokens` are set on
every Groq call: this is a reasoning model (openai/gpt-oss-20b) and on longer
prompts it can burn its entire token budget on internal reasoning, leaving an
empty or truncated `content` field otherwise.
"""

import json
import uuid

from groq import Groq
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import SahayakBaseException
from app.core.logging import get_logger
from app.models.chat_history import ChatHistory
from app.models.enums import LanguageEnum
from app.repositories.chat_repository import ChatRepository
from app.repositories.scheme_repository import SchemeRepository

logger = get_logger(__name__)

_MAX_CONTEXT_SCHEMES = 5
_REASONING_EFFORT = "low"
_MAX_COMPLETION_TOKENS = 4096


class ChatServiceException(SahayakBaseException):
    status_code = 502
    message = "The chat assistant is temporarily unavailable. Please try again."


def _format_context(schemes: list) -> str:
    blocks = []
    for s in schemes:
        blocks.append(
            f"Scheme: {s.name}\n"
            f"State: {s.state or 'Central (nationwide)'}\n"
            f"Category: {s.category.value if s.category else 'N/A'}\n"
            f"Description: {s.full_description or s.short_description or ''}\n"
            f"Benefits: {s.benefits or ''}\n"
            f"Application process: {s.application_process or ''}\n"
            f"Required documents: {s.required_documents or ''}"
        )
    return "\n\n---\n\n".join(blocks)


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._schemes = SchemeRepository(db)
        self._chats = ChatRepository(db)
        self._client = Groq(api_key=settings.GROQ_API_KEY)

    # ── Groq calls ──────────────────────────────────────────────────────

    def _detect_and_translate(self, text: str) -> tuple[LanguageEnum, str]:
        codes = ", ".join(lang.value for lang in LanguageEnum)
        try:
            response = self._client.chat.completions.create(
                model=settings.GROQ_CHAT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a language detection and translation engine. "
                            "Detect the language of the user's text and translate it into English. "
                            f"The detected_lang MUST be one of these ISO codes: {codes}. "
                            "If the text is already in English, set detected_lang to 'en' and "
                            "english_text to the text unchanged. "
                            'Respond ONLY as JSON: {"detected_lang": "<code>", "english_text": "<translation>"}'
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
                reasoning_effort=_REASONING_EFFORT,
                max_completion_tokens=_MAX_COMPLETION_TOKENS,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
        except Exception as exc:
            logger.error("Chat language detection failed: %s", exc)
            raise ChatServiceException() from exc

        try:
            detected_lang = LanguageEnum(data.get("detected_lang", "en"))
        except ValueError:
            detected_lang = LanguageEnum.ENGLISH
        return detected_lang, data.get("english_text", text)

    def _translate(self, text: str, target: LanguageEnum) -> str:
        target_name = target.name.title()
        try:
            response = self._client.chat.completions.create(
                model=settings.GROQ_CHAT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Translate the given text into {target_name}, using its native "
                            "script. Output ONLY the translation, nothing else."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
                reasoning_effort=_REASONING_EFFORT,
                max_completion_tokens=_MAX_COMPLETION_TOKENS,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.error("Chat translation failed: %s", exc)
            raise ChatServiceException() from exc

    def _generate_english_answer(self, english_query: str, context: str) -> str:
        system_prompt = (
            "You are Sahayak, a helpful assistant for Indian government schemes.\n"
            "Use ONLY the following context to answer the user's question.\n"
            "The context may itself be written in a mix of languages: normalize all "
            "information into clear ENGLISH in your answer.\n"
            "Reply ENTIRELY in English.\n"
            "If the answer is not in the context, say "
            "\"I don't have information on that specific scheme right now.\"\n\n"
            f"Context:\n{context}"
        )
        try:
            response = self._client.chat.completions.create(
                model=settings.GROQ_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": english_query},
                ],
                temperature=0.3,
                reasoning_effort=_REASONING_EFFORT,
                max_completion_tokens=_MAX_COMPLETION_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.error("Chat answer generation failed: %s", exc)
            raise ChatServiceException() from exc

    # ── Public API ──────────────────────────────────────────────────────

    async def ask(self, user_id: uuid.UUID, message: str) -> ChatHistory:
        detected_lang, english_query = self._detect_and_translate(message)

        schemes, _total = await self._schemes.search(
            query=english_query, page=1, page_size=_MAX_CONTEXT_SCHEMES
        )
        context = _format_context(schemes)

        english_answer = self._generate_english_answer(english_query, context)
        answer = (
            english_answer
            if detected_lang == LanguageEnum.ENGLISH
            else self._translate(english_answer, detected_lang)
        )

        chat = ChatHistory(
            user_id=user_id,
            question=message,
            answer=answer,
            language=detected_lang,
        )
        return await self._chats.create(chat)

    async def get_history(
        self, user_id: uuid.UUID, *, skip: int = 0, limit: int = 50
    ) -> list[ChatHistory]:
        return await self._chats.get_user_history(user_id, skip=skip, limit=limit)
