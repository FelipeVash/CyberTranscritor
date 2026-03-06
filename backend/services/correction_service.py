# backend/services/correction_service.py
import traceback
from backend.corrector import correct_text

class CorrectionError(Exception):
    """Exceção personalizada para erros de correção com suporte a i18n."""
    def __init__(self, key, **kwargs):
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)

class CorrectionService:
    def __init__(self):
        pass

    def correct(self, text, lang):
        if not text or not text.strip():
            return text
        
        try:
            corrected = correct_text(text, lang)
            return corrected
        except Exception as e:
            error_msg = str(e)
            print(f"Erro na correção: {error_msg}")
            traceback.print_exc()
            raise CorrectionError("correction.error.generic", error=error_msg) from e