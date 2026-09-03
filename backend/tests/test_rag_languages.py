"""
Language resolution / detection tests for the RAG pipeline.

Verifies the hard requirements:
  * all 13 languages detect to their own concrete code
  * Hindi (Devanagari) is never confused with Urdu (Perso-Arabic)
  * Bengali is never confused with Assamese
  * a selected concrete language always wins over auto-detection
  * 'auto' always resolves to one concrete supported code
"""

import pytest

from app.services.rag.languages import (
    SUPPORTED_LANGUAGES,
    answer_in_expected_script,
    detect_text_language,
    normalize_code,
    resolve_language,
)

# One representative sentence per language (PM-KISAN style question).
SAMPLES = {
    "en": "What is the PM Kisan scheme and how do I benefit from it",
    "hi": "प्रधानमंत्री किसान सम्मान निधि योजना क्या है और मुझे कैसे लाभ मिलेगा",
    "ur": "پردھان منتری کسان سمان ندھی اسکیم کیا ہے اور مجھے کیسے فائدہ ملے گا",
    "mr": "मला शेतकरी योजनेचा लाभ कसा मिळेल आणि अर्ज कुठे करायचा आहे",
    "bn": "প্রধানমন্ত্রী কিষান সম্মান নিধি প্রকল্প কী এবং আমি কীভাবে সুবিধা পাব",
    "as": "প্ৰধানমন্ত্ৰী কিষাণ সন্মান নিধি আঁচনি কি আৰু মই কেনেকৈ সুবিধা পাম",
    "ta": "பிரதமர் விவசாயிகள் நல திட்டம் என்றால் என்ன எனக்கு எப்படி பயன் கிடைக்கும்",
    "te": "ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి పథకం అంటే ఏమిటి నాకు ఎలా ప్రయోజనం కలుగుతుంది",
    "gu": "પ્રધાનમંત્રી કિસાન સન્માન નિધિ યોજના શું છે અને મને કેવી રીતે લાભ મળશે",
    "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ ಯೋಜನೆ ಎಂದರೇನು ನನಗೆ ಹೇಗೆ ಲಾಭವಾಗುತ್ತದೆ",
    "ml": "പ്രധാനമന്ത്രി കിസാൻ സമ്മാൻ നിധി പദ്ധതി എന്താണ് എനിക്ക് എങ്ങനെ പ്രയോജനം ലഭിക്കും",
    "pa": "ਪ੍ਰਧਾਨ ਮੰਤਰੀ ਕਿਸਾਨ ਸਨਮਾਨ ਨਿਧੀ ਯੋਜਨਾ ਕੀ ਹੈ ਅਤੇ ਮੈਨੂੰ ਕਿਵੇਂ ਲਾਭ ਮਿਲੇਗਾ",
    "or": "ପ୍ରଧାନମନ୍ତ୍ରୀ କୃଷକ ସମ୍ମାନ ନିଧି ଯୋଜନା କ'ଣ ଏବଂ ମୋତେ କିପରି ଲାଭ ମିଳିବ",
}


def test_registry_has_13_languages():
    assert len(SUPPORTED_LANGUAGES) == 13
    assert set(SUPPORTED_LANGUAGES) == {
        "en", "hi", "ur", "bn", "as", "ta", "te", "mr", "gu", "kn", "ml", "pa", "or"
    }


@pytest.mark.parametrize("code,text", list(SAMPLES.items()))
def test_each_language_detects_to_itself(code, text):
    assert detect_text_language(text) == code


def test_hindi_is_not_urdu():
    assert detect_text_language(SAMPLES["hi"]) == "hi"
    assert detect_text_language(SAMPLES["ur"]) == "ur"
    assert detect_text_language(SAMPLES["hi"]) != detect_text_language(SAMPLES["ur"])


def test_bengali_is_not_assamese():
    assert detect_text_language(SAMPLES["bn"]) == "bn"
    assert detect_text_language(SAMPLES["as"]) == "as"
    assert detect_text_language(SAMPLES["bn"]) != detect_text_language(SAMPLES["as"])


def test_selected_language_overrides_text_language():
    # Question typed in Hindi, but the user picked Tamil → answer must be Tamil.
    code, source = resolve_language(requested="ta", text=SAMPLES["hi"])
    assert (code, source) == ("ta", "selected")


@pytest.mark.parametrize("code", list(SAMPLES.keys()))
def test_selected_language_always_wins(code):
    got, source = resolve_language(requested=code, text=SAMPLES["en"])
    assert got == code
    assert source == "selected"


def test_auto_uses_asr_detected_language():
    code, source = resolve_language(requested="auto", asr_detected="urd", text=None)
    assert (code, source) == ("ur", "asr")


@pytest.mark.parametrize("whisper_label,expected", [
    ("hindi", "hi"), ("tamil", "ta"), ("telugu", "te"), ("marathi", "mr"),
    ("bengali", "bn"), ("assamese", "as"), ("gujarati", "gu"), ("kannada", "kn"),
    ("malayalam", "ml"), ("punjabi", "pa"), ("odia", "or"), ("urdu", "ur"),
    ("english", "en"), ("ta", "ta"), ("en-US", "en"),
])
def test_whisper_language_labels_map_to_asr_source(whisper_label, expected):
    """Whisper emits full names ('tamil') or codes ('ta') — both must resolve
    via the ASR branch, not fall through to text detection."""
    code, source = resolve_language(requested="auto", asr_detected=whisper_label, text="x")
    assert code == expected
    assert source == "asr"


def test_auto_detects_concrete_language_from_text():
    for want in ("bn", "as", "hi", "ur", "ta", "or"):
        code, source = resolve_language(requested="auto", text=SAMPLES[want])
        assert code == want
        assert source == "detected"
        assert code in SUPPORTED_LANGUAGES


def test_auto_never_returns_auto():
    for text in SAMPLES.values():
        code, _ = resolve_language(requested="auto", text=text)
        assert code != "auto"
        assert code in SUPPORTED_LANGUAGES


def test_blank_request_falls_back_to_english():
    assert resolve_language(requested=None, text=None) == ("en", "fallback")
    assert resolve_language(requested="", text="") == ("en", "fallback")


def test_unknown_explicit_code_raises():
    from app.core.exceptions import UnsupportedLanguageException

    with pytest.raises(UnsupportedLanguageException):
        resolve_language(requested="zz", text="hello")


def test_answer_in_expected_script_accepts_native_script():
    assert answer_in_expected_script("पीएम किसान योजना किसानों को पैसा देती है।", "hi")
    assert answer_in_expected_script("প্রধানমন্ত্রী কিষাণ প্রকল্প টাকা দেয়।", "bn")
    assert answer_in_expected_script("پی ایم کسان اسکیم کسانوں کو پیسے دیتی ہے۔", "ur")
    assert answer_in_expected_script("ପିଏମ୍ କିଷାନ ଯୋଜନା କୃଷକଙ୍କୁ ଟଙ୍କା ଦିଏ।", "or")
    assert answer_in_expected_script("PM Kisan gives money to farmers.", "en")


def test_answer_in_expected_script_rejects_romanised():
    # gpt-oss-style romanised Marathi / Hindi must be flagged
    assert not answer_in_expected_script(
        "PM Kisan yojana lahan shetkari kutumbanna dar varshi saha hajar rupaye dete.", "mr"
    )
    assert not answer_in_expected_script(
        "PM Kisan yojana kisano ko paisa deti hai aadhaar card ke saath aavedan karein", "hi"
    )
    # English answer where Urdu was expected
    assert not answer_in_expected_script(
        "PM Kisan scheme gives six thousand rupees to farmer families every year.", "ur"
    )


def test_normalize_code_aliases():
    assert normalize_code("HI") == "hi"
    assert normalize_code("hin") == "hi"
    assert normalize_code("urd") == "ur"
    assert normalize_code("asm") == "as"
    assert normalize_code("pa-IN") == "pa"
    assert normalize_code("bn_BD") == "bn"
    assert normalize_code("zh") is None
