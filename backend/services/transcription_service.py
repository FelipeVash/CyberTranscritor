# backend/services/transcription_service.py
import traceback

class TranscriptionError(Exception):
    """Exceção personalizada para erros de transcrição com suporte a i18n."""
    def __init__(self, key, **kwargs):
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)

class TranscriptionService:
    def __init__(self, model_manager):
        self.model_manager = model_manager

    def transcribe(self, audio, language=None, model_size="tiny"):
        try:
            transcriber = self.model_manager.get_transcriber(model_size)
            result = transcriber.transcribe(audio, language=language)
            
            if result.startswith("[Erro:") or result.startswith("❌"):
                raise TranscriptionError("transcription.error.generic", error=result)
            
            return result
        except TranscriptionError:
            raise
        except Exception as e:
            error_msg = str(e)
            print(f"Erro na transcrição: {error_msg}")
            traceback.print_exc()
            raise TranscriptionError("transcription.error.generic", error=error_msg) from e