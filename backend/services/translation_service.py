# backend/services/translation_service.py
"""
Translation service module.
Handles text translation using the ModelManager.
Defines a custom exception for translation errors.
All logging is done through the centralized logger.
"""

import traceback
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
    """Service for translating text using NLLB models."""

    def __init__(self, model_manager):
        """
        Initialize the translation service.

        Args:
            model_manager: ModelManager instance to obtain translator
        """
        self.model_manager = model_manager
        logger.debug("TranslationService initialized")

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