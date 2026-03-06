# utils/constants.py
"""
Constants used throughout the application.
Includes language mappings, model options, and FLORES codes.
"""

# Supported languages (ISO 639-1 codes)
ALL_LANGUAGES = ["pt", "en", "es", "fr", "it", "de", "zh", "ja", "ko"]
ALL_LANGUAGE_NAMES = {
    "pt": "Português",
    "en": "Inglês",
    "es": "Espanhol",
    "fr": "Francês",
    "it": "Italiano",
    "de": "Alemão",
    "zh": "Chinês",
    "ja": "Japonês",
    "ko": "Coreano"
}

# Mapping for LanguageTool (grammar checker)
LT_LANGUAGE_MAP = {
    "pt": "pt-BR",
    "en": "en-US",
    "es": "es",
    "fr": "fr",
    "it": "it",
    "de": "de-DE",
    "ja": "ja",
    "zh": "zh"
}

# FLORES-200 codes for NLLB translation (kept for compatibility)
FLORES_CODES = {
    "pt": "por_Latn",
    "en": "eng_Latn",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "it": "ita_Latn",
    "ja": "jpn_Jpan",
    "zh": "zho_Hans"
}

# Hunyuan uses its own ISO codes, so no extra mapping needed.