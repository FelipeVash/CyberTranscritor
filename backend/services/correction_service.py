# backend/services/correction_service.py
"""
Grammar correction service module.
Uses LanguageTool via the corrector module.
Defines a custom exception for correction errors.
All logging is done through the centralized logger.
"""

import traceback
from backend.corrector import correct_text
from utils.logger import logger

class CorrectionError(Exception):
    """
    Custom exception for grammar correction errors with i18n support.
    Contains a message key and optional formatting parameters.
    """
    def __init__(self, key, **kwargs):
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)

class CorrectionService:
    """Service for grammar correction of text."""

    def __init__(self):
        """Initialize the correction service."""
        logger.debug("CorrectionService initialized")

    def correct(self, text, lang):
        """
        Correct the grammar of the input text.

        Args:
            text: string to be corrected
            lang: language code (e.g., 'pt', 'en')

        Returns:
            Corrected string.

        Raises:
            CorrectionError: if correction fails and should be reported to user
        """
        if not text or not text.strip():
            logger.debug("Empty text, returning as is")
            return text

        try:
            logger.debug(f"Starting grammar correction (lang={lang})")
            corrected = correct_text(text, lang)
            if corrected != text:
                logger.info("Text corrected successfully")
            else:
                logger.debug("No corrections needed")
            return corrected
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Grammar correction failed: {error_msg}")
            logger.debug(traceback.format_exc())
            # Since correction is non-critical, we raise an exception to allow UI to show error
            raise CorrectionError("correction.error.generic", error=error_msg) from e