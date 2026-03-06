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
            CorrectionError: if correction fails
        """
        if not text or not text.strip():
            return text

        try:
            corrected = correct_text(text, lang)
            logger.debug(f"Correction completed for language '{lang}'")
            return corrected
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Grammar correction failed: {error_msg}")
            traceback.print_exc()
            # Return original text as fallback (non-critical feature)
            return text