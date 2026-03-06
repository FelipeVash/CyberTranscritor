# utils/i18n.py
import json
import locale
import os
from pathlib import Path

class I18n:
    """Gerenciador de internacionalização com suporte a chaves aninhadas."""
    
    def __init__(self, domain="messages", localedir=None):
        self.domain = domain
        self.localedir = localedir or Path(__file__).parent.parent / "locales"
        self.current_language = self._detect_system_language()
        self.translations = {}
        self.load_language(self.current_language)
    
    def _detect_system_language(self):
        """Detecta o idioma do sistema (ex: pt_BR, en_US, es_ES)."""
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
        """Carrega o arquivo de tradução para o idioma especificado."""
        self.current_language = lang_code
        file_path = self.localedir / f"{lang_code}.json"
        
        if not file_path.exists() and lang_code != 'en':
            print(f"Arquivo de idioma {lang_code}.json não encontrado. Usando inglês.")
            file_path = self.localedir / "en.json"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar traduções: {e}")
            self.translations = {}
    
    def get(self, key, **kwargs):
        # Trata pt-br como pt para common.languages
        if key.startswith("common.languages.") and "pt-br" in key:
            key = key.replace("pt-br", "pt")
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

# Instância global
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