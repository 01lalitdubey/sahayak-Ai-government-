"""
RAG / Voice Assistant Schemas — Sahayak AI
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000, description="User question (any supported language)")
    language: str | None = Field(
        default="auto",
        description="Answer/TTS language: one of the 13 codes, or 'auto' to detect.",
    )


class RagSourceItem(BaseModel):
    scheme_id: str
    scheme_code: str
    scheme_name: str
    official_url: str | None = None
    official_pdf_url: str | None = None
    similarity: float
    eligibility_status: str | None = None


class RagAnswerResponse(BaseModel):
    answer: str
    answer_language: str
    answer_language_name: str
    answer_language_native: str
    language_source: str = Field(description="selected | asr | detected | fallback")
    detected_language: str | None = None
    query_language: str
    transcript: str | None = None
    used_query: str
    english_query: str
    grounded: bool
    tts_available: bool
    audio_url: str | None = None
    sources: list[RagSourceItem] = Field(default_factory=list)


class LanguageItem(BaseModel):
    code: str
    english_name: str
    native_name: str
    script: str
    tts_available: bool
    tts_engine: str = "none"  # gtts+mms | gtts | mms | none


class LanguagesResponse(BaseModel):
    auto_supported: bool = True
    languages: list[LanguageItem]


class IngestResponse(BaseModel):
    success: bool = True
    schemes_indexed: int
    collection_size: int


class RagHealthResponse(BaseModel):
    rag_enabled: bool
    asr_enabled: bool
    tts_enabled: bool
    tts_provider: str = "auto"
    tts_languages: int = 0  # languages with at least one working TTS backend
    embedding_model: str
    embedding_dim: int | None = None
    vector_store_path: str
    collection: str
    collection_size: int
    answer_model: str
    translation_model: str
    whisper_model: str
    languages: int
