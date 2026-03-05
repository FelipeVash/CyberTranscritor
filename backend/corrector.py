# backend/corrector.py
import language_tool_python
from utils.constants import LT_LANGUAGE_MAP

def correct_text(text, lang):
    """Corrige o texto usando LanguageTool para o idioma especificado."""
    lt_lang = LT_LANGUAGE_MAP.get(lang, "en-US")
    tool = language_tool_python.LanguageTool(lt_lang)
    return tool.correct(text)