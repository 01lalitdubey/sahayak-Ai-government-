"""
Language registry + resolution + detection — Sahayak AI RAG
===========================================================
Single source of truth for the 13 supported languages plus 'auto'.

Guarantees enforced here:
  * A concrete selected language ALWAYS wins over auto-detection — it controls
    both the answer language and the TTS voice.
  * 'auto' resolves to exactly one concrete supported code, never to 'auto'
    and never to an unsupported language.
  * Hindi (Devanagari) and Urdu (Perso-Arabic) can never collapse into each
    other — they use different scripts and different detection branches.
  * Bengali and Assamese share the Bengali script but are disambiguated by
    Assamese-only letters (ৰ U+09F0, ৱ U+09F1) and a word heuristic, with a
    langdetect fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

AUTO = "auto"


@dataclass(frozen=True)
class LanguageSpec:
    code: str            # app locale / ISO 639-1 (bn, as, ur, ...)
    english_name: str
    native_name: str
    script: str          # human-readable script name
    whisper_code: str    # code Whisper returns / accepts
    indictrans_code: str  # AI4Bharat IndicTrans2 tag (reference only)
    gtts_lang: Optional[str]  # gTTS language code, or None when gTTS lacks it
    # facebook/mms-tts-<mms_model> — offline VITS voice covering ALL 13 languages
    # (this is how Odia/Assamese get real audio; also the fallback for the rest).
    mms_model: Optional[str] = None
    gtts_tld: str = "com"
    # Unicode codepoint ranges that positively identify this script group
    ranges: tuple[tuple[int, int], ...] = field(default_factory=tuple)


# ── The 13 languages ─────────────────────────────────────────────────────────
_DEVANAGARI = ((0x0900, 0x097F),)
_BENGALI = ((0x0980, 0x09FF),)
_GURMUKHI = ((0x0A00, 0x0A7F),)
_GUJARATI = ((0x0A80, 0x0AFF),)
_ORIYA = ((0x0B00, 0x0B7F),)
_TAMIL = ((0x0B80, 0x0BFF),)
_TELUGU = ((0x0C00, 0x0C7F),)
_KANNADA = ((0x0C80, 0x0CFF),)
_MALAYALAM = ((0x0D00, 0x0D7F),)
_ARABIC = (
    (0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
)
_LATIN = ((0x0041, 0x005A), (0x0061, 0x007A))

# positional order: code, english_name, native_name, script, whisper_code,
#                   indictrans_code, gtts_lang, mms_model, gtts_tld, ranges
SUPPORTED_LANGUAGES: dict[str, LanguageSpec] = {
    "en": LanguageSpec("en", "English", "English", "Latin", "en", "eng_Latn", "en", "eng", "co.in", _LATIN),
    "hi": LanguageSpec("hi", "Hindi", "हिन्दी", "Devanagari", "hi", "hin_Deva", "hi", "hin", "co.in", _DEVANAGARI),
    "ur": LanguageSpec("ur", "Urdu", "اردو", "Perso-Arabic", "ur", "urd_Arab", "ur", "urd-script_arabic", "com", _ARABIC),
    "bn": LanguageSpec("bn", "Bengali", "বাংলা", "Bengali", "bn", "ben_Beng", "bn", "ben", "co.in", _BENGALI),
    "as": LanguageSpec("as", "Assamese", "অসমীয়া", "Bengali (Assamese)", "as", "asm_Beng", None, "asm", "com", _BENGALI),
    "ta": LanguageSpec("ta", "Tamil", "தமிழ்", "Tamil", "ta", "tam_Taml", "ta", "tam", "co.in", _TAMIL),
    "te": LanguageSpec("te", "Telugu", "తెలుగు", "Telugu", "te", "tel_Telu", "te", "tel", "co.in", _TELUGU),
    "mr": LanguageSpec("mr", "Marathi", "मराठी", "Devanagari", "mr", "mar_Deva", "mr", "mar", "co.in", _DEVANAGARI),
    "gu": LanguageSpec("gu", "Gujarati", "ગુજરાતી", "Gujarati", "gu", "guj_Gujr", "gu", "guj", "co.in", _GUJARATI),
    "kn": LanguageSpec("kn", "Kannada", "ಕನ್ನಡ", "Kannada", "kn", "kan_Knda", "kn", "kan", "co.in", _KANNADA),
    "ml": LanguageSpec("ml", "Malayalam", "മലയാളം", "Malayalam", "ml", "mal_Mlym", "ml", "mal", "co.in", _MALAYALAM),
    "pa": LanguageSpec("pa", "Punjabi", "ਪੰਜਾਬੀ", "Gurmukhi", "pa", "pan_Guru", "pa", "pan", "co.in", _GURMUKHI),
    "or": LanguageSpec("or", "Odia", "ଓଡ଼ିଆ", "Odia", "or", "ory_Orya", None, "ory", "com", _ORIYA),
}

# Assamese-only letters within the Bengali block (Bengali proper uses র / য)
_ASSAMESE_LETTERS = {"ৰ", "ৱ"}  # ৰ ৱ
_ASSAMESE_HINT_WORDS = ("অসম", "মই", "কৰি", "কৰা", "নাই", "হৈছে", "লগত", "বাবে")
_MARATHI_HINT_WORDS = ("आहे", "आणि", "नाही", "मला", "माझ", "तुम्ही", "ळ", "काय")
_HINDI_HINT_WORDS = ("है", "और", "नहीं", "मैं", "क्या", "हैं", "करने", "लिए")

# Whisper returns either ISO codes ("ta") or full English names ("tamil"); map both.
_ALIASES = {
    # 3-letter ISO-639-2
    "eng": "en", "hin": "hi", "urd": "ur", "ben": "bn", "asm": "as",
    "tam": "ta", "tel": "te", "mar": "mr", "guj": "gu", "kan": "kn",
    "mal": "ml", "pan": "pa", "pnb": "pa", "ori": "or", "ory": "or",
    # full English names (what Whisper's verbose_json usually emits)
    "english": "en", "hindi": "hi", "urdu": "ur", "bengali": "bn",
    "assamese": "as", "tamil": "ta", "telugu": "te", "marathi": "mr",
    "gujarati": "gu", "kannada": "kn", "malayalam": "ml",
    "punjabi": "pa", "panjabi": "pa", "odia": "or", "oriya": "or",
}


def is_supported(code: Optional[str]) -> bool:
    return bool(code) and code.lower() in SUPPORTED_LANGUAGES


def normalize_code(code: Optional[str]) -> Optional[str]:
    """Map an incoming code/alias to one of the 13 supported codes, else None."""
    if not code:
        return None
    c = code.strip().lower().replace("_", "-")
    if c in SUPPORTED_LANGUAGES:
        return c
    base = c.split("-")[0]
    if base in SUPPORTED_LANGUAGES:
        return base
    if base in _ALIASES:
        return _ALIASES[base]
    if c in _ALIASES:
        return _ALIASES[c]
    return None


# ── Script detection ────────────────────────────────────────────────────────

_SCRIPT_GROUPS: tuple[tuple[str, tuple[tuple[int, int], ...]], ...] = (
    ("deva", _DEVANAGARI),
    ("beng", _BENGALI),
    ("guru", _GURMUKHI),
    ("gujr", _GUJARATI),
    ("orya", _ORIYA),
    ("taml", _TAMIL),
    ("telu", _TELUGU),
    ("knda", _KANNADA),
    ("mlym", _MALAYALAM),
    ("arab", _ARABIC),
    ("latn", _LATIN),
)


def _script_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ch in text:
        cp = ord(ch)
        for group, ranges in _SCRIPT_GROUPS:
            if any(lo <= cp <= hi for lo, hi in ranges):
                counts[group] = counts.get(group, 0) + 1
                break
    return counts


def answer_in_expected_script(text: str, lang_code: str) -> bool:
    """
    True when `text` is written in `lang_code`'s own script (Latin for English).
    Used to catch an LLM that romanised/transliterated the answer, which would
    make target-language TTS produce wrong-language speech.
    """
    spec = SUPPORTED_LANGUAGES.get(lang_code)
    if not spec or not text.strip():
        return True
    letters = [ch for ch in text if ch.isalpha()]
    if len(letters) < 8:
        return True
    in_script = sum(
        1 for ch in letters
        if any(lo <= ord(ch) <= hi for lo, hi in spec.ranges)
    )
    return in_script / len(letters) >= 0.5


def _langdetect_guess(text: str) -> Optional[str]:
    try:
        from langdetect import detect_langs  # type: ignore
        from langdetect.lang_detect_exception import LangDetectException  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return None
    try:
        ranked = detect_langs(text)
    except Exception:
        return None
    for item in ranked:
        code = normalize_code(str(item.lang))
        if code:
            return code
    return None


def detect_text_language(text: str) -> str:
    """
    Return exactly one of the 13 supported codes for a piece of text.
    Script-first, then within-script disambiguation, then langdetect, then 'en'.
    """
    if not text or not text.strip():
        return "en"

    counts = _script_counts(text)
    if not counts:
        return "en"

    dominant = max(counts, key=counts.get)  # type: ignore[arg-type]

    if dominant == "arab":
        return "ur"  # Perso-Arabic → Urdu (never Hindi)
    if dominant == "guru":
        return "pa"
    if dominant == "gujr":
        return "gu"
    if dominant == "orya":
        return "or"
    if dominant == "taml":
        return "ta"
    if dominant == "telu":
        return "te"
    if dominant == "knda":
        return "kn"
    if dominant == "mlym":
        return "ml"

    if dominant == "beng":
        # Bengali vs Assamese — same script.
        if any(ch in _ASSAMESE_LETTERS for ch in text):
            return "as"
        if any(w in text for w in _ASSAMESE_HINT_WORDS):
            return "as"
        guess = _langdetect_guess(text)
        return guess if guess in ("bn", "as") else "bn"

    if dominant == "deva":
        # Hindi vs Marathi — same script.
        mr_hits = sum(text.count(w) for w in _MARATHI_HINT_WORDS)
        hi_hits = sum(text.count(w) for w in _HINDI_HINT_WORDS)
        if mr_hits > hi_hits and mr_hits > 0:
            return "mr"
        if hi_hits > 0:
            return "hi"
        guess = _langdetect_guess(text)
        return guess if guess in ("hi", "mr") else "hi"

    if dominant == "latn":
        return "en"

    return "en"


# ── Public resolver ─────────────────────────────────────────────────────────

def resolve_language(
    *,
    requested: Optional[str],
    asr_detected: Optional[str] = None,
    text: Optional[str] = None,
) -> tuple[str, str]:
    """
    Decide the output/TTS language.

    Priority:
      1. `requested` is a concrete supported code  → use it (selection wins).
      2. `requested` is empty/None/'auto':
           a. use the ASR-detected language if it maps to a supported code
           b. else detect from `text`
      3. fallback → 'en'

    Returns (resolved_code, source) where source is one of:
      'selected' | 'asr' | 'detected' | 'fallback'
    """
    req = (requested or "").strip().lower()

    if req and req != AUTO:
        code = normalize_code(req)
        if code:
            return code, "selected"
        # Unknown explicit code → do not silently mistranslate.
        from app.core.exceptions import UnsupportedLanguageException
        raise UnsupportedLanguageException(
            f"'{requested}' is not supported. Supported: "
            f"{', '.join(SUPPORTED_LANGUAGES)} or 'auto'."
        )

    # auto
    if asr_detected:
        code = normalize_code(asr_detected)
        if code:
            return code, "asr"

    if text and text.strip():
        return detect_text_language(text), "detected"

    return "en", "fallback"
