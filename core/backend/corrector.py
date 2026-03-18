# backend/corrector.py
"""
Grammar correction module using LanguageTool.
Provides a simple function to correct text for a given language.
All logging is done through the centralized logger.
"""

import language_tool_python
from core.utils.constants import LT_LANGUAGE_MAP
from core.utils.logger import logger

def correct_text(text, lang):
    """
    Correct the grammar of the input text using LanguageTool.

    Args:
        text: String to be corrected
        lang: Language code (e.g., 'pt', 'en', 'es')

    Returns:
        Corrected string.
    """
    if not text or not text.strip():
        return text

    lt_lang = LT_LANGUAGE_MAP.get(lang, "en-US")
    logger.debug(f"Correcting text with LanguageTool ({lt_lang})")

    try:
        tool = language_tool_python.LanguageTool(lt_lang)
        corrected = tool.correct(text)
        # LanguageTool may return the same string if no errors
        if corrected != text:
            logger.debug("Text was corrected")
        else:
            logger.debug("No corrections needed")
        return corrected
    except Exception as e:
        logger.error(f"LanguageTool error: {e}")
        # Return original text as fallback
        return text