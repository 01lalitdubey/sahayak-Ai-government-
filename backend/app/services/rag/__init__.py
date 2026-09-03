"""
RAG / Voice Assistant package — Sahayak AI
==========================================
Pipeline:
    Voice/Text
      → Whisper (Groq ASR)
      → Language Resolution (selected code wins; 'auto' → detect)
      → allam-2-7b (Groq): user query → English
      → all-MiniLM-L6-v2 embeddings
      → ChromaDB similarity search (top-k scheme chunks)
      → deterministic eligibility rules (for signed-in users with a profile)
      → openai/gpt-oss-120b (Groq): grounded English answer
      → allam-2-7b (Groq): answer → resolved language
      → sources
      → gTTS audio (where the language is supported)
"""

from app.services.rag.languages import (
    SUPPORTED_LANGUAGES,
    LanguageSpec,
    detect_text_language,
    is_supported,
    resolve_language,
)

__all__ = [
    "SUPPORTED_LANGUAGES",
    "LanguageSpec",
    "detect_text_language",
    "is_supported",
    "resolve_language",
]
