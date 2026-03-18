# utils/i18n.py
"""
Internationalization (i18n) module.
Handles translation of UI strings using JSON files.
Supports multiple languages and provides helper functions.
All logging is done through the centralized logger.
"""

import json
import locale
import os
from pathlib import Path
from core.utils.logger import logger

class I18n:
    """Internationalization manager with support for nested keys."""
    
    def __init__(self, domain="messages", localedir=None):
        self.domain = domain
        self.localedir = localedir or Path(__file__).parent.parent / "locales"
        self.current_language = self._detect_system_language()
        self.translations = {}
        self.load_language(self.current_language)
    
    def _detect_system_language(self):
        """Detect system language (e.g., pt_BR, en_US, es_ES)."""
        try:
            lang, _ = locale.getdefaultlocale()
            if lang:
                lang = lang.replace('_', '-').lower()
                if lang.startswith('pt'):
                    return 'pt-br'
                elif lang.startswith('en'):
                    return 'en'
                elif lang.startswith('es'):
                    return 'es'
            return 'en'
        except:
            return 'en'
    
    def load_language(self, lang_code):
        """Load translation file for the specified language."""
        self.current_language = lang_code
        file_path = self.localedir / f"{lang_code}.json"
        
        if not file_path.exists() and lang_code != 'en':
            logger.warning(f"Language file {lang_code}.json not found. Using English.")
            file_path = self.localedir / "en.json"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            logger.info(f"Loaded language: {lang_code}")
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
            self.translations = {}
    
    def get(self, key, **kwargs):
        """Get translated string for key, with optional formatting."""
        # Note: We no longer replace 'pt-br' with 'pt' in language keys.
        # Each language code should have its own entry in the JSON files.
        keys = key.split('.')
        value = self.translations
        try:
            for k in keys:
                value = value[k]
            if isinstance(value, str) and kwargs:
                return value.format(**kwargs)
            return value
        except (KeyError, TypeError):
            return key

    def get_language_display(self, lang_code):
        """
        Return a display string for the language, e.g., "Português (pt-br)".
        Uses the translation of "common.languages.<code>" as the language name.
        """
        name_key = f"common.languages.{lang_code}"
        name = self.get(name_key)
        if name == name_key:
            name = lang_code
        return f"{name} ({lang_code})"

# Global instance
_i18n = I18n()

def _(key, **kwargs):
    return _i18n.get(key, **kwargs)

def set_language(lang_code):
    _i18n.load_language(lang_code)

def get_current_language():
    return _i18n.current_language

def get_available_languages():
    localedir = _i18n.localedir
    files = localedir.glob("*.json")
    return [f.stem for f in files]

def get_language_display(lang_code):
    """
    Global function to get the display representation of a language code.
    """
    return _i18n.get_language_display(lang_code)