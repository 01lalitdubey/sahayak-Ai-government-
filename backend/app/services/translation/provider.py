"""
Translation Provider Interface — Sahayak AI
=============================================
Abstract base class for all translation engine providers.
Ensures Dependency Inversion (SOLID) so the TranslationService
never depends directly on IndicTrans2 or Google.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class TranslationProvider(ABC):
    
    @abstractmethod
    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate a single text string."""
        pass

    @abstractmethod
    async def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        """Translate a batch of text strings efficiently."""
        pass

    @abstractmethod
    async def translate_json(self, data: Dict[str, Any], source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        Translate all string values in a JSON object.
        Preserves keys and structure.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique name of the provider (e.g. 'indictrans2')."""
        pass
