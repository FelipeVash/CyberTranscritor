# backend/services/translation_service.py
import traceback

class TranslationError(Exception):
    """Exceção personalizada para erros de tradução com suporte a i18n."""
    def __init__(self, key, **kwargs):
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)

class TranslationService:
    def __init__(self, model_manager):
        self.model_manager = model_manager

    def translate(self, text, source_lang="pt", target_lang="en"):
        if not text or not text.strip():
            return ""
        
        try:
            translator = self.model_manager.get_translator(source_lang, target_lang)
            result = translator.translate(text)
            
            if result.startswith("[Erro:") or result.startswith("❌"):
                raise TranslationError("translation.error.generic", error=result)
            
            return result
        except TranslationError:
            raise
        except Exception as e:
            error_msg = str(e)
            print(f"Erro na tradução ({source_lang}->{target_lang}): {error_msg}")
            traceback.print_exc()
            raise TranslationError("translation.error.generic", 
                                  source=source_lang, 
                                  target=target_lang, 
                                  error=error_msg) from e