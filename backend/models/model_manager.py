# backend/models/model_manager.py
"""
Model lifecycle manager.
Handles loading, caching, and automatic unloading of AI models (transcriber, translator).
All logging is done through the centralized logger.
"""

import torch
import threading
import time
from backend.transcriber import TranscriberGPU
from backend.translator import Translator
from utils.logger import logger

class ModelManager:
    """
    Manages model instances (transcriber and translator).
    Maintains a single instance per model type and unloads after inactivity.
    """

    def __init__(self, device="cuda", idle_timeout=60):
        """
        Initialize the model manager.

        Args:
            device: Inference device ('cuda' or 'cpu')
            idle_timeout: Seconds of inactivity before unloading models
        """
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.idle_timeout = idle_timeout

        # Current models
        self.current_transcriber = None
        self.current_transcriber_model = None
        self.current_translator = None
        self.current_translator_pair = (None, None)

        # Unload timer
        self.unload_timer = None
        self.lock = threading.RLock()
        self.last_access = time.time()

        logger.info(f"ModelManager initialized (device={self.device}, idle_timeout={idle_timeout}s)")

    def _reset_timer(self):
        """Reset the idle timer."""
        with self.lock:
            if self.unload_timer:
                self.unload_timer.cancel()
            self.unload_timer = threading.Timer(self.idle_timeout, self._unload_if_idle)
            self.unload_timer.daemon = True
            self.unload_timer.start()

    def _unload_if_idle(self):
        """Unload models if idle timeout has been reached."""
        with self.lock:
            if time.time() - self.last_access >= self.idle_timeout:
                logger.info("Idle timeout reached, unloading models")
                self.unload_all()
                self.unload_timer = None
            else:
                # If not idle yet, restart timer with remaining time
                remaining = self.idle_timeout - (time.time() - self.last_access)
                if remaining > 0:
                    self.unload_timer = threading.Timer(remaining, self._unload_if_idle)
                    self.unload_timer.daemon = True
                    self.unload_timer.start()

    def _update_access(self):
        """Update last access time and restart timer."""
        with self.lock:
            self.last_access = time.time()
            self._reset_timer()

    def get_transcriber(self, model_size="tiny"):
        """
        Return the transcriber, loading if needed or if model size changed.

        Args:
            model_size: Whisper model size

        Returns:
            TranscriberGPU instance
        """
        with self.lock:
            self._update_access()
            if (self.current_transcriber is None) or (self.current_transcriber_model != model_size):
                self.unload_transcriber()
                logger.info(f"Loading transcriber model {model_size}")
                self.current_transcriber = TranscriberGPU(model_size=model_size, device=self.device)
                self.current_transcriber_model = model_size
            return self.current_transcriber

    def get_translator(self, source_lang="pt", target_lang="en"):
        """
        Return the translator, loading if needed or if parameters changed.

        Args:
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translator instance
        """
        with self.lock:
            self._update_access()
            if (self.current_translator is None or
                self.current_translator_pair != (source_lang, target_lang)):
                self.unload_translator()
                logger.info(f"Loading translator {source_lang} -> {target_lang}")
                try:
                    self.current_translator = Translator(
                        source_lang=source_lang,
                        target_lang=target_lang,
                        device=self.device
                    )
                    self.current_translator_pair = (source_lang, target_lang)
                except Exception as e:
                    logger.error(f"Failed to load translator: {e}")
                    raise
            return self.current_translator

    def unload_transcriber(self):
        """Unload the transcriber from GPU."""
        with self.lock:
            if self.current_transcriber:
                logger.debug("Unloading transcriber")
                del self.current_transcriber
                self.current_transcriber = None
                self.current_transcriber_model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    def unload_translator(self):
        """Unload the translator from GPU."""
        with self.lock:
            if self.current_translator:
                logger.debug("Unloading translator")
                self.current_translator.unload()
                del self.current_translator
                self.current_translator = None
                self.current_translator_pair = (None, None)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    def unload_all(self):
        """Unload all models."""
        with self.lock:
            self.unload_transcriber()
            self.unload_translator()
            if self.unload_timer:
                self.unload_timer.cancel()
                self.unload_timer = None
            logger.info("All models unloaded")

    def __del__(self):
        self.unload_all()