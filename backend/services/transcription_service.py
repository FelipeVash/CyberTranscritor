# backend/services/transcription_service.py
"""
Transcription service module.
Handles audio transcription using the ModelManager.
Defines a custom exception for transcription errors.
All logging is done through the centralized logger.
"""

import traceback
from utils.logger import logger

class TranscriptionError(Exception):
    """
    Custom exception for transcription errors with i18n support.
    Contains a message key and optional formatting parameters.
    """
    def __init__(self, key, **kwargs):
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)

class TranscriptionService:
    """Service for transcribing audio using Whisper models."""

    def __init__(self, model_manager):
        """
        Initialize the transcription service.

        Args:
            model_manager: ModelManager instance to obtain transcriber
        """
        self.model_manager = model_manager
        logger.debug("TranscriptionService initialized")

    def transcribe(self, audio, language=None, model_size="tiny"):
        """
        Transcribe the provided audio.

        Args:
            audio: numpy array with audio (16kHz, mono)
            language: language code (e.g., 'pt') or None for auto-detection
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')

        Returns:
            String with transcribed text.

        Raises:
            TranscriptionError: if transcription fails
        """
        try:
            transcriber = self.model_manager.get_transcriber(model_size)
            result = transcriber.transcribe(audio, language=language)

            # Check if result indicates an error
            if result.startswith("[Erro:") or result.startswith("❌"):
                logger.error(f"Transcription returned error: {result}")
                raise TranscriptionError("transcription.error.generic", error=result)

            return result
        except TranscriptionError:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Transcription failed: {error_msg}")
            traceback.print_exc()
            raise TranscriptionError("transcription.error.generic", error=error_msg) from e