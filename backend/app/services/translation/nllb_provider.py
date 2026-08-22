"""
Meta NLLB-200 Translation Provider — Sahayak AI
=================================================
Production-grade offline translation engine using Meta's NLLB-200.
Implements the TranslationProvider interface.
Uses Singleton pattern to avoid repeated PyTorch model loading.
"""

import logging
from typing import Any, Dict, List
import asyncio

try:
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except ImportError:
    torch = None
    AutoModelForSeq2SeqLM = None
    AutoTokenizer = None

from app.services.translation.provider import TranslationProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

# ISO 639-1 / 639-2 to NLLB language token mapping
# Sahayak supported languages
LANGUAGE_MAPPING = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "mr": "mar_Deva",
    "gu": "guj_Gujr",
    "bn": "ben_Beng",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "pa": "pan_Guru",
    "or": "ory_Orya",
    "as": "asm_Beng",
}

class NLLBProvider(TranslationProvider):
    _instance = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLLBProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_initialized:
            if not torch:
                raise ImportError("PyTorch and Transformers are required for NLLBProvider.")
            
            self._device = self._detect_device()
            self._model_name = settings.NLLB_MODEL
            self._batch_size = settings.TRANSLATION_BATCH_SIZE
            
            logger.info(f"Loading NLLB-200 Model: {self._model_name} on {self._device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self._model_name).to(self._device)
            logger.info("NLLB-200 Model loaded successfully.")
            
            NLLBProvider._is_initialized = True

    def _detect_device(self) -> str:
        device_setting = settings.TRANSLATION_DEVICE.lower()
        if device_setting == "auto":
            if torch.cuda.is_available():
                return "cuda"
            # Optional: MPS for Apple Silicon
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return device_setting

    @property
    def provider_name(self) -> str:
        return "nllb"
        
    @property
    def memory_usage_mb(self) -> float:
        if self._device == "cuda" and torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 * 1024)
        return 0.0

    def _get_nllb_lang(self, lang_code: str) -> str:
        return LANGUAGE_MAPPING.get(lang_code, "eng_Latn")

    def _validate_translation(self, original: str, translated: str, target_lang: str) -> str:
        """Apply rules to reject bad translations."""
        if not translated:
            return original
        
        translated = translated.strip()
        
        if not translated:
            return original
            
        # Reject if translation is exactly the same as original for indic languages
        if original == translated and target_lang != "en":
            # For extremely short texts (numbers, etc.), it might be fine, but generally for schemes it's a failure
            if len(original) > 5:
                logger.warning(f"Translation returned identical text: {original[:20]}...")
                return original
                
        # Additional checks can be added here (e.g. valid unicode sequences)
        return translated

    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text or not text.strip():
            return text
            
        results = await self.translate_batch([text], source_lang, target_lang)
        return results[0] if results else text

    async def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        if not texts:
            return []
            
        src_lang = self._get_nllb_lang(source_lang)
        tgt_lang = self._get_nllb_lang(target_lang)
        
        # Since this blocks the event loop with heavy compute, we run it in a thread executor
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._run_inference_batch, texts, src_lang, tgt_lang)

    def _run_inference_batch(self, texts: list[str], src_lang: str, tgt_lang: str) -> list[str]:
        """Synchronous CPU/GPU inference logic."""
        self.tokenizer.src_lang = src_lang
        
        # Split into batches
        all_translations = []
        
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]
            valid_batch = [t if t and t.strip() else " " for t in batch]
            
            inputs = self.tokenizer(valid_batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            forced_bos_token_id = self.tokenizer.lang_code_to_id[tgt_lang]
            
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=forced_bos_token_id,
                    max_length=512,
                    num_beams=4,
                )
                
            decoded = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            
            for j, orig in enumerate(batch):
                if not orig or not orig.strip():
                    all_translations.append(orig)
                else:
                    target_lang_code = [k for k, v in LANGUAGE_MAPPING.items() if v == tgt_lang][0]
                    validated = self._validate_translation(orig, decoded[j], target_lang_code)
                    all_translations.append(validated)
                    
            # Clear CUDA cache if applicable
            if self._device == "cuda":
                torch.cuda.empty_cache()
                
        return all_translations

    async def translate_json(self, data: Dict[str, Any], source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        Extract strings, batch translate them, and reconstruct the JSON.
        """
        if not data:
            return {}

        keys_to_translate = []
        values_to_translate = []
        
        for k, v in data.items():
            if isinstance(v, str) and v.strip():
                keys_to_translate.append(k)
                values_to_translate.append(v)
            
        if not values_to_translate:
            return data
            
        translated_values = await self.translate_batch(values_to_translate, source_lang, target_lang)
        
        result = dict(data)
        for k, tv in zip(keys_to_translate, translated_values):
            result[k] = tv
            
        return result
