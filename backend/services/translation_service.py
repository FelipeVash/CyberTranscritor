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
    Cache keys include model size to differentiate between fast and precise translations.
    """
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _make_key(self, text, source_lang, target_lang, model_size):
        """Create a unique cache key including model size."""
        return (source_lang, target_lang, model_size, text)

    def get(self, text, source_lang, target_lang, model_size):
        """Return cached translation if exists, else None."""
        key = self._make_key(text, source_lang, target_lang, model_size)
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            logger.debug(f"Cache hit for {source_lang}->{target_lang} (model={model_size})")
            return self.cache[key]
        self.misses += 1
        logger.debug(f"Cache miss for {source_lang}->{target_lang} (model={model_size})")
        return None

    def put(self, text, source_lang, target_lang, model_size, translation):
        """Store translation in cache."""
        key = self._make_key(text, source_lang, target_lang, model_size)
        self.cache[key] = translation
        self.cache.move_to_end(key)
        if len(self.cache) > self.max_size:
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
        This method obtains a translator from the model manager and uses it.

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

        # Obtain translator (will load appropriate model)
        translator = self.model_manager.get_translator(source_lang, target_lang)
        return self.translate_with_translator(translator, text)

    def translate_with_translator(self, translator, text):
        """
        Translate text using a provided translator instance, with caching.
        This method is used when the translator is already obtained (e.g., for lazy loading).

        Args:
            translator: Translator instance
            text: string to be translated

        Returns:
            Translated string.

        Raises:
            TranslationError: if translation fails
        """
        if not text or not text.strip():
            logger.debug("Empty text, returning empty string")
            return ""

        source = translator.source_lang
        target = translator.target_lang
        model_size = translator.model_size

        # Check cache first
        cached = self.cache.get(text, source, target, model_size)
        if cached is not None:
            return cached

        try:
            logger.debug(f"Starting translation with {model_size}: {source} -> {target}")
            result = translator.translate(text)

            # Check if result indicates an error
            if result.startswith("[Error:") or result.startswith("❌"):
                logger.error(f"Translation returned error: {result}")
                raise TranslationError("translation.error.generic",
                                      source=source,
                                      target=target,
                                      error=result)

            # Store in cache
            self.cache.put(text, source, target, model_size, result)

            logger.info(f"Translation completed: {source} -> {target} ({model_size})")
            return result
        except TranslationError:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Translation failed ({source}->{target}): {error_msg}")
            logger.debug(traceback.format_exc())
            raise TranslationError("translation.error.generic",
                                  source=source,
                                  target=target,
                                  error=error_msg) from e

    def clear_cache(self):
        """Clear the translation cache."""
        self.cache.clear()

    def cache_stats(self):
        """Return cache statistics."""
        return self.cache.stats()