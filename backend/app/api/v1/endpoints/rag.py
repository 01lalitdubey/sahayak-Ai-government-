"""
RAG / Voice Assistant Endpoints — Sahayak AI
============================================
Public:
    GET  /api/v1/rag/languages       — the 13 supported languages + 'auto'
    GET  /api/v1/rag/health          — pipeline configuration / index status
    POST /api/v1/rag/query           — text question  → localized answer + sources
    POST /api/v1/rag/voice           — speech question → localized answer + sources + audio
    GET  /api/v1/rag/audio/{name}    — fetch a generated TTS clip (mp3 or wav)
Admin:
    POST /api/v1/rag/ingest          — (re)build the ChromaDB scheme index

Auth is OPTIONAL on /query and /voice: anonymous users get answers without
personalised eligibility; signed-in users additionally get deterministic
eligibility results folded into the answer and the sources.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Form, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import oauth2_scheme, require_admin
from app.auth.token import verify_access_token, extract_user_id
from app.core.config import settings
from app.core.exceptions import RagDisabledException, ValidationException
from app.core.logging import get_logger
from app.database.database import get_db
from app.models.user import User
from app.schemas.rag import (
    IngestResponse,
    LanguageItem,
    LanguagesResponse,
    RagAnswerResponse,
    RagHealthResponse,
    RagQueryRequest,
)
from app.services.rag import embeddings, tts, vector_store
from app.services.rag.languages import SUPPORTED_LANGUAGES
from app.services.rag.pipeline import RagPipeline

logger = get_logger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG Assistant"])

_MAX_AUDIO_BYTES = 25 * 1024 * 1024  # Groq Whisper hard limit


async def get_optional_user_id(
    token: str | None = Depends(oauth2_scheme),
) -> uuid.UUID | None:
    """Resolve the caller's user id from a Bearer token if present; never 401."""
    if not token:
        return None
    try:
        payload = verify_access_token(token)
        return uuid.UUID(extract_user_id(payload))
    except Exception:  # noqa: BLE001 - anonymous is a valid state here
        return None


# ── Metadata endpoints ─────────────────────────────────────────────────────

@router.get("/languages", response_model=LanguagesResponse, summary="Supported languages")
async def list_languages() -> LanguagesResponse:
    return LanguagesResponse(
        auto_supported=True,
        languages=[
            LanguageItem(
                code=s.code,
                english_name=s.english_name,
                native_name=s.native_name,
                script=s.script,
                tts_available=tts.tts_supported(s.code),
                tts_engine=(
                    "gtts+mms" if s.gtts_lang and s.mms_model
                    else "gtts" if s.gtts_lang
                    else "mms" if s.mms_model
                    else "none"
                ),
            )
            for s in SUPPORTED_LANGUAGES.values()
        ],
    )


@router.get("/health", response_model=RagHealthResponse, summary="RAG pipeline health")
async def rag_health() -> RagHealthResponse:
    try:
        size = vector_store.count()
    except Exception:  # noqa: BLE001
        size = 0
    return RagHealthResponse(
        rag_enabled=settings.rag_enabled,
        asr_enabled=settings.RAG_ENABLE_ASR,
        tts_enabled=settings.RAG_ENABLE_TTS,
        tts_provider=settings.RAG_TTS_PROVIDER,
        tts_languages=sum(1 for s in SUPPORTED_LANGUAGES if tts.tts_supported(s)),
        embedding_model=settings.RAG_EMBEDDING_MODEL,
        embedding_dim=embeddings.dimension(),
        vector_store_path=settings.RAG_CHROMA_PATH,
        collection=settings.RAG_COLLECTION,
        collection_size=size,
        answer_model=settings.GROQ_ANSWER_MODEL,
        translation_model=settings.GROQ_TRANSLATION_MODEL,
        whisper_model=settings.GROQ_WHISPER_MODEL,
        languages=len(SUPPORTED_LANGUAGES),
    )


# ── Query endpoints ────────────────────────────────────────────────────────

@router.post("/query", response_model=RagAnswerResponse, summary="Ask a text question")
async def rag_query(
    payload: RagQueryRequest,
    user_id: uuid.UUID | None = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
) -> RagAnswerResponse:
    if not settings.rag_enabled:
        raise RagDisabledException()
    result = await RagPipeline(db).run(
        query_text=payload.query,
        requested_language=payload.language,
        user_id=user_id,
    )
    return RagAnswerResponse(**result.to_dict())


@router.post("/voice", response_model=RagAnswerResponse, summary="Ask a spoken question")
async def rag_voice(
    audio: UploadFile = File(..., description="Audio clip (webm/ogg/mp3/wav/m4a)"),
    language: str = Form("auto", description="Answer/TTS language code or 'auto'"),
    user_id: uuid.UUID | None = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
) -> RagAnswerResponse:
    if not settings.rag_enabled:
        raise RagDisabledException()
    if not settings.RAG_ENABLE_ASR:
        raise ValidationException("Voice input is disabled on this server.")
    raw = await audio.read()
    if not raw:
        raise ValidationException("Empty audio upload.")
    if len(raw) > _MAX_AUDIO_BYTES:
        raise ValidationException("Audio too large (max 25 MB).")
    result = await RagPipeline(db).run(
        audio=raw,
        audio_filename=audio.filename or "audio.webm",
        requested_language=language,
        user_id=user_id,
    )
    return RagAnswerResponse(**result.to_dict())


@router.get("/audio/{name}", summary="Fetch a generated TTS clip")
async def rag_audio(name: str) -> FileResponse:
    path = tts.audio_path(name)
    if path is None:
        raise ValidationException("Audio not found or expired.")
    # mp3 (gTTS) or wav (MMS) — same route, correct content-type either way.
    return FileResponse(path, media_type=tts.media_type_for(name), filename=name)


# ── Admin: index management ────────────────────────────────────────────────

@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="(Re)build the scheme vector index [Admin]",
)
async def rag_ingest(
    rebuild: bool = True,
    _: User = Depends(require_admin),
) -> IngestResponse:
    from app.services.rag.ingest import build_index

    out = await build_index(rebuild=rebuild)
    return IngestResponse(
        schemes_indexed=out["schemes"],
        collection_size=out["chunks"],
    )
