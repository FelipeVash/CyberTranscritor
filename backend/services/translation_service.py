"""
Translation service module.
Handles text translation using the ModelManager with caching.
Defines a custom exception for translation errors.
All logging is done through the centralized logger.
"""

import traceback
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


class TranslationCache:
    """
    LRU cache for translations.
    Stores up to max_size entries, discarding least recently used when full.
    """
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _make_key(self, text, source_lang, target_lang):
        """Create a unique cache key."""
        # Use a tuple as key (hashable)
        return (source_lang, target_lang, text)

    def get(self, text, source_lang, target_lang):
        """Return cached translation if exists, else None."""
        key = self._make_key(text, source_lang, target_lang)
        if key in self.cache:
            # Move to end to mark as recently used
            self.cache.move_to_end(key)
            self.hits += 1
            logger.debug(f"Cache hit for {source_lang}->{target_lang}")
            return self.cache[key]
        self.misses += 1
        logger.debug(f"Cache miss for {source_lang}->{target_lang}")
        return None

    def put(self, text, source_lang, target_lang, translation):
        """Store translation in cache."""
        key = self._make_key(text, source_lang, target_lang)
        self.cache[key] = translation
        self.cache.move_to_end(key)
        if len(self.cache) > self.max_size:
            # Remove least recently used (first item)
            removed = self.cache.popitem(last=False)
            logger.debug(f"Cache full, removed oldest entry: {removed[0]}")

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Translation cache cleared")

    def stats(self):
        """Return cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses
        }


class TranslationService:
    """Service for translating text using NLLB models with caching."""

    def __init__(self, model_manager, cache_size=1000):
        """
        Initialize the translation service.

        Args:
            model_manager: ModelManager instance to obtain translator
            cache_size: Maximum number of translations to cache (default: 1000)
        """
        self.model_manager = model_manager
        self.cache = TranslationCache(max_size=cache_size)
        logger.debug(f"TranslationService initialized with cache size {cache_size}")

    def translate(self, text, source_lang="pt", target_lang="en"):
        """
        Translate text from source_lang to target_lang, using cache if possible.

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

        # Check cache first
        cached = self.cache.get(text, source_lang, target_lang)
        if cached is not None:
            return cached

        try:
            logger.debug(f"Starting translation: {source_lang} -> {target_lang}")
            translator = self.model_manager.get_translator(source_lang, target_lang)
            result = translator.translate(text)

            # Check if result indicates an error
            if result.startswith("[Error:") or result.startswith("❌"):
                logger.error(f"Translation returned error: {result}")
                raise TranslationError("translation.error.generic",
                                      source=source_lang,
                                      target=target_lang,
                                      error=result)

            # Store in cache
            self.cache.put(text, source_lang, target_lang, result)

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

    def clear_cache(self):
        """Clear the translation cache."""
        self.cache.clear()

    def cache_stats(self):
        """Return cache statistics."""
        return self.cache.stats()