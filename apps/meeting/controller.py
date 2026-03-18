# ======================================================================
# ARQUIVO: apps/meeting/controller.py
# ======================================================================
"""
Meeting controller for the independent meeting recorder.
Manages audio capture, offline diarization using pyannote.audio 4.0+.
All logging is done through the centralized logger.
"""

import threading
import tempfile
import tkinter.messagebox as messagebox
from pathlib import Path
import numpy as np
import os
import torch
from pyannote.audio import Pipeline
from core.utils.logger import logger
from core.backend.audio.capture import AudioCapture

class MeetingController:
    """
    Controller for meeting recording and processing.
    """

    def __init__(self, window):
        self.window = window
        self.audio_capture = None
        self.pipeline = None
        self.current_speaker = None
        self.recording = False
        self.audio_file = None

    def list_sinks(self):
        """Return list of audio sinks."""
        capture = AudioCapture()
        sinks = capture.list_sinks()
        capture.pulse.close()
        return sinks

    def start_recording(self, sink_name):
        """Start recording from selected sink."""
        self.audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.audio_file.close()
        self.audio_capture = AudioCapture()

        token = os.getenv("HUGGINGFACE_TOKEN")
        if not token:
            logger.error("HUGGINGFACE_TOKEN environment variable not set.")
            self.window.root.after(
                0,
                lambda: messagebox.showerror(
                    "Erro",
                    "A variável de ambiente HUGGINGFACE_TOKEN não está definida.\n"
                    "Ela é necessária para baixar o modelo de diarização.",
                    parent=self.window.root
                )
            )
            return

        # Autenticação (opcional, pois o token será passado diretamente)
        os.environ["HUGGINGFACE_HUB_TOKEN"] = token

        try:
            logger.info("Carregando pipeline pyannote/speaker-diarization-community-1...")
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-community-1",
                token=token
            )
            if torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
                logger.info("Pipeline movido para GPU")
            logger.info("Pipeline carregado com sucesso")
        except Exception as e:
            logger.error(f"Falha ao carregar pipeline: {e}")
            self.window.root.after(
                0,
                lambda: messagebox.showerror(
                    "Erro",
                    f"Não foi possível carregar o pipeline:\n{str(e)}",
                    parent=self.window.root
                )
            )
            return

        self.audio_capture.start(sink_name, self.audio_file.name, self._audio_callback)
        self.recording = True
        logger.info("Gravação iniciada")

    def _audio_callback(self, chunk):
        """Apenas armazena o áudio (processamento será offline)."""
        pass

    def stop_recording(self):
        """Para a gravação e inicia o processamento offline, se aplicável."""
        if self.audio_capture is not None:
            self.audio_capture.stop()
            self.audio_capture = None

        self.recording = False

        if self.audio_file is None:
            logger.info("Nenhuma gravação foi iniciada. Ignorando processamento.")
            self.window.show_processing(False)
            return

        logger.info("Processando áudio com pyannote...")
        self.window.show_processing(True)
        threading.Thread(target=self._offline_processing, daemon=True).start()

    def _offline_processing(self):
        """Aplica o pipeline ao arquivo gravado e exibe o resultado."""
        try:
            if self.audio_file is None:
                logger.error("Arquivo de áudio não existe.")
                return

            diarization = self.pipeline(self.audio_file.name)
            result_text = "Diarização:\n"
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                result_text += f"{turn.start:.1f}s - {turn.end:.1f}s: {speaker}\n"

            self.window.root.after(0, self.window.display_transcript, result_text)
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            self.window.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.window.root.after(0, self.window.show_processing, False)