"""
TTS provider abstraction + language router — Sahayak AI RAG
==========================================================
Replaces the gTTS-only path with pluggable providers so every one of the 13
languages has a working voice — including Odia and Assamese, which gTTS cannot
speak.

Providers (see ``TtsProvider``):
  * GttsProvider — Google Translate TTS. Fast, no model, needs internet at
    request time. Covers 11/13 (no Odia, no Assamese).
  * MmsProvider  — facebook/mms-tts-<iso3> VITS models via transformers. Fully
    offline once downloaded. Covers ALL 13 (native scripts; Urdu uses the
    Perso-Arabic MMS checkpoint). This is how or/as/ur get real speech and it
    NEVER substitutes another language.

The router (``synthesize``) picks an ordered provider chain per language from
``settings.RAG_TTS_PROVIDER`` and always keeps MMS as the final fallback, so a
transient gTTS failure can never leave a language silent.
"""

from __future__ import annotations

import io
import re
import threading
import time
import wave
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.rag.languages import SUPPORTED_LANGUAGES, LanguageSpec

logger = get_logger(__name__)


class TtsError(RuntimeError):
    """A single provider failed to synthesize."""


# ── Provider interface ────────────────────────────────────────────────────────
class TtsProvider(ABC):
    name: str = "base"
    audio_ext: str = "mp3"  # container of the bytes returned by synthesize()

    @abstractmethod
    def supports(self, lang_code: str) -> bool:
        ...

    @abstractmethod
    def synthesize(self, text: str, lang_code: str) -> bytes:
        """Return audio bytes (self.audio_ext container). Raise TtsError on failure."""


# ── gTTS ────────────────────────────────────────────────────────────────────
class GttsProvider(TtsProvider):
    name = "gtts"
    audio_ext = "mp3"

    def supports(self, lang_code: str) -> bool:
        spec = SUPPORTED_LANGUAGES.get(lang_code)
        return bool(spec and spec.gtts_lang)

    def synthesize(self, text: str, lang_code: str) -> bytes:
        spec = SUPPORTED_LANGUAGES[lang_code]
        try:
            from gtts import gTTS  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise TtsError(f"gTTS not installed: {exc}") from exc
        buf = io.BytesIO()
        try:
            gTTS(text=text, lang=spec.gtts_lang, tld=spec.gtts_tld, slow=False).write_to_fp(buf)
        except Exception as exc:
            raise TtsError(f"gTTS synthesis failed for {lang_code}: {exc}") from exc
        data = buf.getvalue()
        if len(data) < 512:
            raise TtsError(f"gTTS returned {len(data)} bytes for {lang_code}")
        return data


# ── MMS-TTS (facebook/mms-tts-*) ────────────────────────────────────────────
_SENT_SPLIT = re.compile(r"(?<=[।॥\.!\?؟…])\s+|\n+")


class MmsProvider(TtsProvider):
    name = "mms"
    audio_ext = "wav"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # lang_code -> (tokenizer, model, sampling_rate); LRU-capped
        self._cache: "OrderedDict[str, tuple]" = OrderedDict()
        self._uroman = None
        self._uroman_tried = False

    def supports(self, lang_code: str) -> bool:
        spec = SUPPORTED_LANGUAGES.get(lang_code)
        return bool(spec and spec.mms_model)

    # -- model loading ------------------------------------------------------
    def _load(self, spec: LanguageSpec):
        code = spec.code
        with self._lock:
            hit = self._cache.get(code)
            if hit is not None:
                self._cache.move_to_end(code)
                return hit
            try:
                import torch  # noqa: F401
                from transformers import AutoTokenizer, VitsModel  # type: ignore
            except Exception as exc:  # pragma: no cover
                raise TtsError(f"transformers/torch unavailable: {exc}") from exc

            model_id = f"facebook/mms-tts-{spec.mms_model}"
            logger.info("Loading MMS-TTS %s for '%s' ...", model_id, code)
            t0 = time.time()
            tok = AutoTokenizer.from_pretrained(model_id, cache_dir=settings.RAG_TTS_MMS_CACHE_DIR)
            mdl = VitsModel.from_pretrained(model_id, cache_dir=settings.RAG_TTS_MMS_CACHE_DIR)
            mdl.eval()
            sr = int(mdl.config.sampling_rate)
            logger.info("MMS-TTS %s ready (%.1fs, sr=%d, uroman=%s)",
                        code, time.time() - t0, sr, getattr(tok, "is_uroman", False))
            entry = (tok, mdl, sr)
            self._cache[code] = entry
            while len(self._cache) > max(1, settings.RAG_TTS_MMS_MAX_MODELS):
                evicted, _ = self._cache.popitem(last=False)
                logger.info("Evicted MMS-TTS model for '%s' (LRU)", evicted)
            return entry

    def _romanize(self, text: str) -> str:
        """Only used for MMS checkpoints whose tokenizer sets is_uroman=True."""
        if not self._uroman_tried:
            self._uroman_tried = True
            try:
                import uroman as _ur  # type: ignore
                self._uroman = _ur.Uroman()
            except Exception:
                self._uroman = None
        if self._uroman is None:
            return text
        try:
            return self._uroman.romanize_string(text)
        except Exception:
            return text

    def synthesize(self, text: str, lang_code: str) -> bytes:
        spec = SUPPORTED_LANGUAGES.get(lang_code)
        if not spec or not spec.mms_model:
            raise TtsError(f"no MMS model mapped for {lang_code}")
        import numpy as np
        import torch

        tok, mdl, sr = self._load(spec)
        need_uroman = bool(getattr(tok, "is_uroman", False))

        # VITS degrades on long inputs — synthesize sentence chunks and concat.
        chunks = [c.strip() for c in _SENT_SPLIT.split(text) if c.strip()]
        if not chunks:
            chunks = [text.strip()]
        merged: list[np.ndarray] = []
        gap = np.zeros(int(sr * 0.18), dtype=np.float32)
        acc = ""
        batched: list[str] = []
        for c in chunks:
            if len(acc) + len(c) < 400:
                acc = f"{acc} {c}".strip()
            else:
                if acc:
                    batched.append(acc)
                acc = c
        if acc:
            batched.append(acc)

        for piece in batched:
            src = self._romanize(piece) if need_uroman else piece
            inputs = tok(src, return_tensors="pt")
            try:
                with torch.no_grad():
                    wav = mdl(**inputs).waveform
            except Exception as exc:
                raise TtsError(f"MMS inference failed for {lang_code}: {exc}") from exc
            arr = wav.squeeze().detach().cpu().numpy().astype(np.float32)
            if arr.size:
                merged.append(arr)
                merged.append(gap)

        if not merged:
            raise TtsError(f"MMS produced no audio for {lang_code}")
        audio = np.concatenate(merged)
        peak = float(np.abs(audio).max()) if audio.size else 0.0
        if audio.size < sr * 0.3 or peak < 0.01:
            raise TtsError(f"MMS output too short/silent for {lang_code} (peak={peak:.3f})")
        # normalise a touch and write 16-bit PCM WAV
        if peak > 0:
            audio = audio / max(peak, 0.2) * 0.95
        pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm.tobytes())
        return buf.getvalue()


# ── singletons + router ─────────────────────────────────────────────────────
_gtts = GttsProvider()
_mms = MmsProvider()


def provider_chain(lang_code: str) -> list[TtsProvider]:
    """Ordered providers to try for a language. MMS is always the last resort so
    Odia/Assamese (and anything gTTS drops transiently) still speak."""
    mode = (settings.RAG_TTS_PROVIDER or "auto").lower()
    chain: list[TtsProvider] = []
    if mode == "mms":
        chain = [_mms]
    elif mode == "gtts":
        chain = [_gtts]
    else:  # auto
        if _gtts.supports(lang_code):
            chain = [_gtts]
    # MMS as the guaranteed fallback for every supported language
    if _mms.supports(lang_code) and _mms not in chain:
        chain.append(_mms)
    return [p for p in chain if p.supports(lang_code)]


def any_provider_supports(lang_code: str) -> bool:
    return bool(provider_chain(lang_code))


def synthesize_bytes(text: str, lang_code: str) -> Optional[tuple[bytes, str, str]]:
    """Try each provider (with retries). Returns (audio_bytes, ext, provider_name)
    or None only if every provider failed."""
    text = (text or "").strip()[: settings.RAG_TTS_MAX_CHARS]
    if not text:
        return None
    retries = max(1, settings.RAG_TTS_RETRIES)
    for provider in provider_chain(lang_code):
        last: Exception | None = None
        for attempt in range(retries):
            try:
                data = provider.synthesize(text, lang_code)
                if data:
                    return data, provider.audio_ext, provider.name
            except Exception as exc:  # noqa: BLE001 - fall through to next provider
                last = exc
                time.sleep(0.5 * (attempt + 1))
        logger.warning("TTS provider '%s' failed for %s after %d tries: %s",
                       provider.name, lang_code, retries, last)
    logger.error("All TTS providers failed for language '%s'", lang_code)
    return None
