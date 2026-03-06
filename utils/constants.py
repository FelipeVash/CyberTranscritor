# utils/constants.py
"""
Constants used throughout the application.
Includes language mappings, model options, FLORES codes, TTS voices, and translation models.
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

# FLORES-200 codes for NLLB translation
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

# Available Piper TTS voices
TTS_VOICES = {
    # Portuguese voices
    "pt_BR-faber-medium": "Português (Brasil) - Faber (médio)",
    "pt_BR-cadu-medium": "Português (Brasil) - Cadu (médio)",
    "pt_BR-jeff-medium": "Português (Brasil) - Jeff (médio)",
    "pt_PT-tugao-medium": "Português (Portugal) - Tugão (médio)",
    
    # Spanish voices [citation:2][citation:3][citation:8]
    "es_ES-carlfm-x_low": "Espanhol (Espanha) - CarlFM (baixo)",
    "es_ES-davefx-medium": "Espanhol (Espanha) - DaveFX (médio)",
    "es_ES-marta-medium": "Espanhol (Espanha) - Marta (médio)",
    "es_MX-claude-high": "Espanhol (México) - Claude (alto)",
    "es_AR-daniela-high": "Espanhol (Argentina) - Daniela (alto)",
    
    # Chinese voices [citation:3][citation:5][citation:8]
    "zh_CN-huayan-medium": "Chinês (China) - Huayan (médio)",
    "zh_CN-huayan-x_low": "Chinês (China) - Huayan (baixo)",
    
    # English voices
    "en_US-lessac-medium": "Inglês (EUA) - Lessac (médio)",
    "en_US-amy-medium": "Inglês (EUA) - Amy (médio)",
    "en_GB-alan-medium": "Inglês (Reino Unido) - Alan (médio)",
    "en_GB-southern_english_female-medium": "Inglês (Reino Unido) - Sul feminino (médio)",
    
    # Other languages
    "fr_FR-upmc-medium": "Francês (França) - UPMC (médio)",
    "de_DE-thorsten-medium": "Alemão (Alemanha) - Thorsten (médio)",
    "it_IT-paola-medium": "Italiano (Itália) - Paola (médio)",
    "ja_JP-kyoko-medium": "Japonês (Japão) - Kyoko (médio)",
    "ko_KR-sunhi-medium": "Coreano (Coreia do Sul) - Sunhi (médio)"
}

# Available NLLB translation models
TRANSLATION_MODELS = {
    "nllb-200M": "NLLB-200M (rápido, menos preciso)",
    "nllb-600M": "NLLB-600M",
    "nllb-1.3B": "NLLB-1.3B",
    "nllb-3.3B": "NLLB-3.3B (preciso, recomendado)"
}