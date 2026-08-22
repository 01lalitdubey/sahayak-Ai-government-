"""
IndicTrans2 Translation Provider — Sahayak AI
===============================================
Implementation of the TranslationProvider using AI4Bharat IndicTrans2.
Features:
- Local caching in models/indictrans2
- Automatic GPU (CUDA/MPS) vs CPU detection
- Batched inference with torch.no_grad()
- Rejects empty, whitespace, identical, or invalid translations.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from app.core.config import settings
from app.services.translation.provider import TranslationProvider
from app.services.translation.IndicTransToolkit.processor import IndicProcessor

log = logging.getLogger("indictrans2_provider")

class IndicTrans2Provider(TranslationProvider):
    
    # Centralized language mapping from frontend locales to IndicTrans2 codes
    LANG_MAPPING = {
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
    
    _instance = None
    _model = None
    _tokenizer = None
    _device = None
    _ip = None

    def __new__(cls):
        """Singleton pattern to ensure model is loaded only once."""
        if cls._instance is None:
            cls._instance = super(IndicTrans2Provider, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization if already loaded
        if self._model is not None:
            return
            
        self.model_name = settings.TRANSLATION_MODEL_NAME
        # The prompt asked for MODEL_CACHE_DIR, which I mapped in settings.
        self.cache_dir = getattr(settings, "MODEL_CACHE_DIR", "models/indictrans2")
        self.device_config = settings.TRANSLATION_DEVICE
        self.initialize()

    def initialize(self):
        """Load model and tokenizer into memory."""
        self._device = self.detect_device()
        
        log.info(f"Initializing IndicTrans2 Provider on {self._device}...")
        log.info(f"Model: {self.model_name}, Cache Dir: {self.cache_dir}")
        
        # Ensure cache dir exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        try:
            self._ip = IndicProcessor(inference=True)
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                cache_dir=self.cache_dir, 
                src_lang="eng_Latn",
                trust_remote_code=True
            )
            
            # Load model with mixed precision if CUDA
            kwargs = {}
            if self._device.type == "cuda":
                kwargs["torch_dtype"] = torch.float16
            
            self._model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name, 
                cache_dir=self.cache_dir,
                trust_remote_code=True,
                **kwargs
            )
            
            self._model.to(self._device)
            self._model.eval()
            
            log.info("IndicTrans2 Model loaded successfully.")
            self.model_info()
            
        except Exception as e:
            log.error(f"Failed to load IndicTrans2 model: {e}")
            raise e

    def detect_device(self) -> torch.device:
        """Automatically detect the best available hardware."""
        if self.device_config != "auto":
            return torch.device(self.device_config)
            
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")

    def model_info(self):
        """Log details about the loaded model and environment."""
        log.info("=== IndicTrans2 Model Info ===")
        log.info(f"Selected Device: {self._device}")
        log.info(f"Torch Version: {torch.__version__}")
        if self._device.type == "cuda":
            log.info(f"GPU Name: {torch.cuda.get_device_name(self._device)}")
            log.info(f"CUDA Version: {torch.version.cuda}")
            vram_gb = torch.cuda.get_device_properties(self._device).total_memory / (1024**3)
            log.info(f"Total VRAM: {vram_gb:.2f} GB")
        log.info("==============================")

    def shutdown(self):
        """Cleanup resources."""
        if self._model:
            del self._model
            self._model = None
        if self._tokenizer:
            del self._tokenizer
            self._tokenizer = None
        if self._ip:
            del self._ip
            self._ip = None
        if self._device and self._device.type == "cuda":
            torch.cuda.empty_cache()
        log.info("IndicTrans2 resources released.")

    @property
    def provider_name(self) -> str:
        return "indictrans2"

    def _is_valid_translation(self, original: str, translated: str) -> bool:
        """Reject empty, whitespace-only, or identical-to-English translations."""
        if not translated or not translated.strip():
            return False
        
        # Reject if identical (assuming source is English, target is Indic)
        if original.strip().lower() == translated.strip().lower():
            # If the original text is purely alphanumeric/punctuation, we might allow it
            if len(original) > 5 and original.isascii():
                return False
                
        # Reject if translation is just punctuation
        import string
        if all(char in string.punctuation or char.isspace() for char in translated):
            return False
            
        # Reject if the translation is exceptionally short compared to original without reason
        if len(translated) < (len(original) * 0.1) and len(original) > 20:
             return False

        return True

    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text or not text.strip():
            return ""
        results = await self.translate_batch([text], source_lang, target_lang)
        return results[0] if results else ""

    async def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        """Translate a batch of strings efficiently using optimized inference."""
        if not texts:
            return []
            
        # Get target language token
        tgt_lang_code = self.LANG_MAPPING.get(target_lang)
        if not tgt_lang_code:
            log.warning(f"Unsupported target language: {target_lang}")
            return texts
            
        # Filter empty strings but keep their indices
        to_translate = []
        indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                to_translate.append(text)
                indices.append(i)
                
        if not to_translate:
            return ["" for _ in texts]

        results = [""] * len(texts)
        
        # Run inference in threadpool since model.generate is blocking CPU/GPU bound
        try:
            loop = asyncio.get_running_loop()
            
            src_lang_code = self.LANG_MAPPING.get(source_lang, "eng_Latn")
            
            translated_chunks = await loop.run_in_executor(
                None, 
                self._run_inference_batch, 
                to_translate, 
                src_lang_code,
                tgt_lang_code
            )
            
            # Map back to original indices and validate
            for i, translated in zip(indices, translated_chunks):
                original = texts[i]
                if self._is_valid_translation(original, translated):
                    results[i] = translated
                else:
                    log.warning(f"Translation validation failed. Keeping original text. Original: '{original[:20]}...'")
                    results[i] = original
                    
        except Exception as e:
            log.error(f"Batch translation failed: {e}")
            # In case of failure (e.g. OOM), return original strings
            return texts
            
        return results
        
    def _run_inference_batch(self, texts: List[str], src_lang_code: str, tgt_lang_code: str) -> List[str]:
        """Synchronous inference method to be run in executor."""
        # IndicProcessor handles language tag prepending and script normalization
        batch = self._ip.preprocess_batch(texts, src_lang=src_lang_code, tgt_lang=tgt_lang_code)

        inputs = self._tokenizer(
            batch, 
            truncation=True, 
            padding=True, 
            max_length=512, 
            return_tensors="pt"
        )
        
        # Move to device
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        
        with torch.no_grad():
            generated_tokens = self._model.generate(
                **inputs,
                max_length=512,
                num_beams=4,
            )
            
        decoded_preds = self._tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
        
        # Reconstruct valid UTF-8 strings from decoded subwords using IndicProcessor
        final_preds = self._ip.postprocess_batch(decoded_preds, lang=tgt_lang_code)
        return final_preds

    async def translate_json(self, data: Dict[str, Any], source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Translate all string values in a JSON object using batching."""
        if not data:
            return {}

        keys_to_translate = []
        values_to_translate = []
        
        for k, v in data.items():
            if isinstance(v, str) and v.strip() and k not in ["uuid", "id", "url", "code", "phone", "email"]:
                keys_to_translate.append(k)
                values_to_translate.append(v)
            
        if not values_to_translate:
            return data
            
        translated_values = await self.translate_batch(values_to_translate, source_lang, target_lang)
        
        result = dict(data)
        for k, tv in zip(keys_to_translate, translated_values):
            result[k] = tv
            
        return result

    async def health_check(self) -> bool:
        """Check if model is loaded and responding."""
        try:
            return self._model is not None and self._tokenizer is not None
        except Exception:
            return False
