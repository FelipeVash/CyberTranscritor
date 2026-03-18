# backend/background/background_recorder.py
"""
Background recording module.
Handles audio capture when the application is minimized (triggered by Super+0).
Detects silence, transcribes, and queries DeepSeek.
Results are shown as notifications or by opening the DeepSeek window.
All logging is done through the centralized logger.
"""

import threading
import numpy as np
from core.backend.audio.recorder import AudioRecorder
from core.backend.deepseek_client import DeepSeekClient
from core.utils.i18n import _
from core.utils.logger import logger
from core import config
import traceback

class BackgroundRecorder:
    """
    Manages background recording (activated by Super+0).
    Captures audio, detects silence, transcribes, and queries DeepSeek.
    The result is displayed as a notification or by opening the DeepSeek window.
    """

    def __init__(self, controller):
        """
        Initialize the background recorder.

        Args:
            controller: Reference to the AppController (to access UI and services)
        """
        self.controller = controller
        self.recording = False
        self.recorder = None
        self.timer = None
        self.silence_timeout = 5  # seconds of silence to stop
        self.audio_buffer = []

    def start(self):
        """Start background recording."""
        if self.recording:
            logger.warning("Background recording already in progress")
            return
        logger.info("Starting background recording")
        self.recording = True
        self.audio_buffer = []
        self.recorder = AudioRecorder(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            blocksize=1600,
            callback=self._on_audio_chunk
        )
        self.recorder.start()
        self.controller.show_notification(
            _("tray.notifications.background_start_title"),
            _("tray.notifications.background_start")
        )
        self._reset_timer()

    def stop(self, from_timer=False):
        """
        Stop recording and process the captured audio.

        Args:
            from_timer: True if called by silence timeout, False if called manually
        """
        if not self.recording:
            return
        logger.info("Stopping background recording")
        self.recording = False
        if self.timer:
            self.timer.cancel()
            self.timer = None
        audio = self.recorder.stop()
        if audio.size == 0:
            if from_timer:
                self.controller.show_notification(
                    _("tray.notifications.background_timeout_title"),
                    _("tray.notifications.background_timeout")
                )
            else:
                self.controller.show_notification(
                    _("tray.notifications.background_no_audio_title"),
                    _("tray.notifications.background_no_audio")
                )
            return
        self.controller.show_notification(
            _("tray.notifications.background_processing_title"),
            _("tray.notifications.background_processing")
        )
        self._process_audio(audio)

    def _on_audio_chunk(self, chunk):
        """Callback called for each audio chunk."""
        self.audio_buffer.append(chunk)
        self._reset_timer()

    def _reset_timer(self):
        """Reset the silence timer."""
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.silence_timeout, lambda: self.stop(from_timer=True))
        self.timer.daemon = True
        self.timer.start()

    def _process_audio(self, audio):
        """
        Process the audio: transcribe and query DeepSeek.
        If the response is short, show a notification; otherwise open the DeepSeek window.
        """
        def task():
            try:
                # Transcribe audio
                transcriber = self.controller.transcriber  # uses the controller's transcriber
                logger.debug("Transcribing background audio")
                text = transcriber.transcribe(audio, language=self.controller.current_language.get())
                if text.startswith("[Erro:") or text.startswith("❌") or "áudio muito baixo" in text.lower():
                    # Use controller's centralized error handling
                    self.controller.root.after(0, lambda: self.controller._handle_service_error(
                        Exception(text), "deepseek_window.messages.transcription_error"
                    ))
                    return

                # Query DeepSeek
                logger.debug("Querying DeepSeek with transcribed text")
                client = DeepSeekClient()
                resposta = client.ask(text, opt_out=True)

                # Decide how to present the response
                if len(resposta) < 300 and '```' not in resposta and '    ' not in resposta:
                    # Short response: show as notification
                    self.controller.root.after(0, lambda: self.controller.show_notification(
                        _("tray.notifications.deepseek_response_title"),
                        resposta[:200] + ("..." if len(resposta) > 200 else "")
                    ))
                    # Optionally speak the response via TTS
                    if hasattr(self.controller, 'tts_engine') and self.controller.tts_engine:
                        threading.Thread(target=self.controller.tts_engine.speak, args=(resposta,), daemon=True).start()
                else:
                    # Long response: open DeepSeek window with context
                    self.controller.root.after(0, lambda: self.controller.open_deepseek_with_context(text, resposta))
            except Exception as e:
                logger.error(f"Error processing background audio: {e}")
                logger.debug(traceback.format_exc())
                self.controller.root.after(0, lambda: self.controller._handle_service_error(
                    e, "deepseek_window.messages.deepseek_error", error=str(e)
                ))

        threading.Thread(target=task, daemon=True).start()