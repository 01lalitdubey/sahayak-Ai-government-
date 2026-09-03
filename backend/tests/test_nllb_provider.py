import pytest
import sys
from unittest.mock import MagicMock, patch

# QUARANTINED (see tests/conftest.py collect_ignore): this module assigns
# sys.modules['torch'] / sys.modules['transformers'] at import time and never
# restores them, contaminating every other test in the session. It also asserts
# against a singleton API the provider no longer exposes (_instance /
# _is_initialized). Needs a rewrite with proper monkeypatch fixtures before it
# can be re-enabled.

# Mock torch and transformers before importing the provider
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False
mock_torch.cuda.memory_allocated.return_value = 0
mock_torch.backends.mps.is_available.return_value = False

mock_transformers = MagicMock()
mock_transformers.AutoTokenizer.from_pretrained.return_value = MagicMock()
mock_transformers.AutoModelForSeq2SeqLM.from_pretrained.return_value = MagicMock()

sys.modules['torch'] = mock_torch
sys.modules['transformers'] = mock_transformers

from app.services.translation.nllb_provider import NLLBProvider
from app.core.config import settings

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton instance between tests."""
    NLLBProvider._instance = None
    NLLBProvider._is_initialized = False
    yield

def test_singleton_pattern():
    provider1 = NLLBProvider()
    provider2 = NLLBProvider()
    
    assert provider1 is provider2
    assert provider1._is_initialized is True

def test_language_mapping():
    provider = NLLBProvider()
    
    assert provider._get_nllb_lang("hi") == "hin_Deva"
    assert provider._get_nllb_lang("te") == "tel_Telu"
    assert provider._get_nllb_lang("en") == "eng_Latn"
    assert provider._get_nllb_lang("unknown_lang") == "eng_Latn"

def test_device_fallback():
    # Force settings to 'auto' and torch cuda to False
    settings.TRANSLATION_DEVICE = "auto"
    mock_torch.cuda.is_available.return_value = False
    
    provider = NLLBProvider()
    assert provider._device == "cpu"

def test_validate_translation_rejects_empty():
    provider = NLLBProvider()
    
    # Should return original if translation is empty
    result = provider._validate_translation("Hello", "", "hi")
    assert result == "Hello"
    
    # Should return original if translation is whitespace
    result = provider._validate_translation("Hello", "   ", "hi")
    assert result == "Hello"

def test_validate_translation_rejects_identical_indic():
    provider = NLLBProvider()
    
    # Same string, but translating to Hindi (indic). Should be rejected because it's too long to be a simple untranslatable word.
    result = provider._validate_translation("Government Scheme Name", "Government Scheme Name", "hi")
    assert result == "Government Scheme Name"
    
    # Same string, but short. Might be accepted.
    result = provider._validate_translation("Hi", "Hi", "hi")
    assert result == "Hi"

@pytest.mark.asyncio
async def test_translate_text_empty():
    provider = NLLBProvider()
    
    result = await provider.translate_text("", "en", "hi")
    assert result == ""
    
    result = await provider.translate_text("   ", "en", "hi")
    assert result == "   "
