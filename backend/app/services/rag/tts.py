"""
Text-to-speech facade — Sahayak AI RAG
======================================
Public surface used by the pipeline / endpoints is unchanged:

    await synthesize(text, lang_code) -> filename | None
    tts_supported(lang_code) -> bool
    audio_path(name) -> Path | None

The actual work is delegated to a provider chain (see ``tts_providers``):
gTTS where it has a voice, and facebook/mms-tts-* (offline VITS) otherwise and
as a fallback — so all 13 languages, Odia and Assamese included, produce audio.
Generated files are ``<uuid>.mp3`` (gTTS) or ``<uuid>.wav`` (MMS); the
``/api/v1/rag/audio/{name}`` route serves either with the right content-type.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.rag import tts_providers

logger = get_logger(__name__)

_AUDIO_EXTS = (".mp3", ".wav")
_MEDIA_TYPES = {".mp3": "audio/mpeg", ".wav": "audio/wav"}


def _audio_dir() -> Path:
    d = Path(settings.RAG_AUDIO_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def tts_supported(lang_code: str) -> bool:
    """True when at least one TTS provider can speak this language.
    With MMS in the chain this is True for all 13 supported languages."""
    return tts_providers.any_provider_supports(lang_code)


def media_type_for(name: str) -> str:
    return _MEDIA_TYPES.get(Path(name).suffix.lower(), "application/octet-stream")


def _cleanup(dir_: Path) -> None:
    ttl = settings.RAG_AUDIO_TTL_MINUTES * 60
    now = time.time()
    for ext in _AUDIO_EXTS:
        for f in dir_.glob(f"*{ext}"):
            try:
                if now - f.stat().st_mtime > ttl:
                    f.unlink(missing_ok=True)
            except OSError:
                pass


def _synth_sync(text: str, lang_code: str) -> Optional[str]:
    if not text or not text.strip():
        return None
    result = tts_providers.synthesize_bytes(text, lang_code)
    if result is None:
        return None
    data, ext, provider = result
    dir_ = _audio_dir()
    _cleanup(dir_)
    name = f"{uuid.uuid4().hex}.{ext.lstrip('.')}"
    path = dir_ / name
    try:
        path.write_bytes(data)
    except OSError as exc:
        logger.error("Could not write TTS file %s: %s", name, exc)
        return None
    if not path.is_file() or path.stat().st_size == 0:
        return None
    logger.info("TTS ok: lang=%s provider=%s file=%s (%d bytes)",
                lang_code, provider, name, len(data))
    return name


async def synthesize(text: str, lang_code: str) -> Optional[str]:
    """Return the audio filename (served by GET /rag/audio/{name}) or None."""
    if not settings.RAG_ENABLE_TTS:
        return None
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _synth_sync, text, lang_code)


def audio_path(name: str) -> Optional[Path]:
    """Resolve a served filename to a path, guarding against traversal."""
    if not name or "/" in name or "\\" in name or ".." in name:
        return None
    if Path(name).suffix.lower() not in _AUDIO_EXTS:
        return None
    p = _audio_dir() / name
    return p if p.is_file() else None
