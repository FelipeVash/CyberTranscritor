# utils/constants.py
# Idiomas suportados (códigos ISO 639-1)
ALL_LANGUAGES = ["pt", "en", "es", "fr", "it", "de", "zh", "ja", "ko"]
ALL_LANGUAGE_NAMES = {
    "pt": "Português", "en": "Inglês", "es": "Espanhol", "fr": "Francês",
    "it": "Italiano", "de": "Alemão", "zh": "Chinês", "ja": "Japonês", "ko": "Coreano"
}

# Mapeamento para LanguageTool (corretor gramatical)
LT_LANGUAGE_MAP = {
    "pt": "pt-BR", "en": "en-US", "es": "es", "fr": "fr",
    "it": "it", "de": "de-DE", "ja": "ja", "zh": "zh"
}

# Mapeamento para NLLB (mantido por compatibilidade, mas não usado se migrar completamente)
FLORES_CODES = {
    "pt": "por_Latn",
    "en": "eng_Latn",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "it": "ita_Latn",
    "ja": "jpn_Jpan",
    "zh": "zho_Hans",
    "ko": "kor_Hang"  # se suportado
}

# Hunyuan usa os próprios códigos ISO, então não precisa mapeamento extra.