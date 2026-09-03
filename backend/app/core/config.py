"""
Core Configuration — Sahayak AI Backend
=========================================
Pydantic v2 BaseSettings — type-safe, env-driven, cached singleton.
All secrets loaded from environment variables / .env file.
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────
    APP_NAME: str = Field(default="Sahayak AI")
    APP_VERSION: str = Field(default="0.1.0")
    APP_ENV: str = Field(default="development")  # development | staging | production

    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(default="change-me-in-production-use-a-long-random-string")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sahayak:sahayak_password@localhost:5432/sahayak_db"
    )
    # Override SQL echo — defaults to True in dev, False in prod
    DATABASE_ECHO: bool = Field(default=False)
    # Connection pool
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: int = Field(default=30)    # seconds to wait for a free connection
    DB_POOL_RECYCLE: int = Field(default=1800)  # recycle connections after 30 min

    # ── CORS ──────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # ── Logging ───────────────────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO")

    # ── Translation Infrastructure ────────────────────────────────────────
    TRANSLATION_PROVIDER: str = Field(default="indictrans2")
    TRANSLATION_MODEL_NAME: str = Field(default="prajdabre/rotary-indictrans2-en-indic-dist-200M")
    TRANSLATION_BATCH_SIZE: int = Field(default=8)
    TRANSLATION_DEVICE: str = Field(default="auto")
    MODEL_CACHE_DIR: str = Field(default="models/indictrans2")
    TRANSLATION_MAX_RETRIES: int = Field(default=3)

    # ── RAG / Voice Assistant (Groq + ChromaDB + all-MiniLM-L6-v2) ─────────
    # Groq hosts Whisper (ASR) and gpt-oss (translation + answers) behind an
    # OpenAI-compatible REST API. A single API key drives all of it.
    GROQ_API_KEY: str = Field(default="")
    GROQ_BASE_URL: str = Field(default="https://api.groq.com/openai/v1")
    GROQ_WHISPER_MODEL: str = Field(default="whisper-large-v3")
    # Query→English translation for retrieval. gpt-oss handles all 13 languages
    # well; allam-2-7b does NOT (Arabic-only) and produces degenerate Indic output.
    GROQ_TRANSLATION_MODEL: str = Field(default="openai/gpt-oss-20b")
    # Answers are generated DIRECTLY in the resolved language by this model.
    GROQ_ANSWER_MODEL: str = Field(default="openai/gpt-oss-120b")
    RAG_REQUEST_TIMEOUT: float = Field(default=60.0)

    # Retrieval
    RAG_EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    RAG_CHROMA_MODE: str = Field(default="local")  # local | persistent | http
    RAG_CHROMA_PATH: str = Field(default="chroma_db")
    RAG_CHROMA_HOST: str = Field(default="localhost")
    RAG_CHROMA_PORT: int = Field(default=8001)
    RAG_COLLECTION: str = Field(default="sahayak_schemes")
    RAG_TOP_K: int = Field(default=3)
    RAG_MAX_QUERY_CHARS: int = Field(default=1000)
    RAG_MIN_SCORE: float = Field(default=0.0)  # cosine similarity floor (0 = keep all)

    # Voice
    RAG_ENABLE_ASR: bool = Field(default=True)
    RAG_ENABLE_TTS: bool = Field(default=True)
    RAG_AUDIO_DIR: str = Field(default="app/static/rag_audio")
    RAG_AUDIO_TTL_MINUTES: int = Field(default=120)

    # TTS provider routing:
    #   "auto" — gTTS where it has a voice, MMS (facebook/mms-tts-*) otherwise
    #            and always as a fallback → every one of the 13 languages speaks
    #   "gtts" — gTTS first, MMS fallback (keeps Odia/Assamese working)
    #   "mms"  — offline MMS VITS for all 13 (no request-time internet)
    RAG_TTS_PROVIDER: str = Field(default="auto")
    RAG_TTS_MMS_CACHE_DIR: str = Field(default=".cache/hf_tts")
    RAG_TTS_MMS_MAX_MODELS: int = Field(default=6)   # LRU cap on loaded VITS models
    RAG_TTS_MAX_CHARS: int = Field(default=1200)     # answer text cap fed to TTS
    RAG_TTS_RETRIES: int = Field(default=3)

    # ── Computed properties ───────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    @property
    def should_echo_sql(self) -> bool:
        """Echo SQL in dev unless DATABASE_ECHO explicitly set to False."""
        if self.DATABASE_ECHO:
            return True
        return self.is_development

    @property
    def rag_enabled(self) -> bool:
        """RAG needs a Groq API key to reach Whisper / allam / gpt-oss."""
        return bool(self.GROQ_API_KEY and self.GROQ_API_KEY.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached settings singleton — imported everywhere as:
        from app.core.config import settings
    """
    return Settings()


settings = get_settings()
