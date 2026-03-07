"""
Translation service module.
Handles text translation using the ModelManager.
Defines a custom exception for translation errors.
All logging is done through the centralized logger.
"""

import traceback
import threading
from collections import OrderedDict
from utils.logger import logger

class TranslationError(Exception):
    """
    Custom exception for translation errors with i18n support.
    Contains a message key and optional formatting parameters.
    """
    def __init__(self, key, **kwargs):
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)

class TranslationService:
    """Service for translating text using NLLB models with caching."""

    def __init__(self, model_manager):
        """
        Initialize the translation service.

        Args:
            model_manager: ModelManager instance to obtain translator
        """
        self.model_manager = model_manager
        self.cache = OrderedDict()
        self.cache_maxsize = 1000
        self.cache_lock = threading.RLock()
        logger.debug("TranslationService initialized with cache (maxsize=1000)")

    def _normalize_text(self, text):
        """Normalize text for consistent cache keys."""
        # Remove leading/trailing spaces and collapse multiple spaces
        return ' '.join(text.strip().split())

    def _get_cache_key(self, text, source_lang, target_lang):
        """Generate a cache key from translation parameters."""
        normalized = self._normalize_text(text)
        return (normalized, source_lang, target_lang)

    def translate(self, text, source_lang="pt", target_lang="en"):
        """
        Translate text from source_lang to target_lang.

        Args:
            text: string to be translated
            source_lang: source language code
            target_lang: target language code

        Returns:
            Translated string.

        Raises:
            TranslationError: if translation fails
        """
        if not text or not text.strip():
            logger.debug("Empty text, returning empty string")
            return ""

        key = self._get_cache_key(text, source_lang, target_lang)

        # Check cache (thread-safe)
        with self.cache_lock:
            if key in self.cache:
                # Move to end to mark as recently used
                self.cache.move_to_end(key)
                logger.debug(f"Cache hit for {source_lang}->{target_lang}")
                return self.cache[key]

        logger.debug(f"Cache miss for {source_lang}->{target_lang}")

        try:
            translator = self.model_manager.get_translator(source_lang, target_lang)
            result = translator.translate(text)

            # Check if result indicates an error
            if result.startswith("[Error:") or result.startswith("❌"):
                logger.error(f"Translation returned error: {result}")
                raise TranslationError("translation.error.generic",
                                      source=source_lang,
                                      target=target_lang,
                                      error=result)

            # Store in cache only if successful (thread-safe)
            with self.cache_lock:
                self.cache[key] = result
                if len(self.cache) > self.cache_maxsize:
                    # Remove oldest item (first in OrderedDict)
                    self.cache.popitem(last=False)
                    logger.debug("Cache maxsize reached, removed oldest item")

            logger.info(f"Translation completed: {source_lang} -> {target_lang}")
            return result

        except TranslationError:
            # Already logged, re-raise
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Translation failed ({source_lang}->{target_lang}): {error_msg}")
            logger.debug(traceback.format_exc())
            raise TranslationError("translation.error.generic",
                                  source=source_lang,
                                  target=target_lang,
                                  error=error_msg) from e