# ======================================================================
# ARQUIVO: controller/meeting_controller.py
# ======================================================================
"""
Meeting controller for the independent meeting recorder.
Uses pyannote.audio 4.0+ for reliable speaker diarization.
"""

import threading
import tempfile
import tkinter.messagebox as messagebox
from pathlib import Path
import numpy as np
import os
import torch
from diart.sources import AudioSource
from utils.logger import logger
from backend.audio.capture import AudioCapture
from backend.models.model_manager import ModelManager

# pyannote 4.0: importação correta do pipeline
from pyannote.audio import Pipeline

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
        self.model_manager = ModelManager()  # útil para outros modelos

    def list_sinks(self):
        """Return list of audio sinks."""
        capture = AudioCapture()
        sinks = capture.list_sinks()
        capture.pulse.close()
        return sinks

    def start_recording(self, sink_name):
        """Start recording from selected sink and begin diarization."""
        self.audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.audio_file.close()
        self.audio_capture = AudioCapture()

        # Obter o token do ambiente
        token = os.getenv("HUGGINGFACE_TOKEN")
        if not token:
            logger.error("HUGGINGFACE_TOKEN environment variable not set.")
            self.window.root.after(
                0,
                lambda: messagebox.showerror(
                    "Erro",
                    "A variável de ambiente HUGGINGFACE_TOKEN não está definida.",
                    parent=self.window.root
                )
            )
            return

        # Definir também HUGGINGFACE_HUB_TOKEN (compatibilidade)
        os.environ["HUGGINGFACE_HUB_TOKEN"] = token

        try:
            # pyannote 4.0: carregar o pipeline community-1 com token
            # Nota: o parâmetro 'use_auth_token' foi substituído por 'token' [citation:3]
            logger.info("Carregando pipeline pyannote/speaker-diarization-community-1...")
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-community-1",
                token=token  # ← parâmetro correto no pyannote 4.0
            )

            # Mover para GPU se disponível
            if torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
                logger.info("Pipeline movido para GPU")

            logger.info("Pipeline carregado com sucesso")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Falha ao carregar pipeline: {error_msg}")
            self.window.root.after(
                0,
                lambda err=error_msg: messagebox.showerror(
                    "Erro",
                    f"Não foi possível carregar o pipeline de diarização:\n{err}\n\n"
                    "Verifique se você aceitou os termos em:\n"
                    "https://huggingface.co/pyannote/speaker-diarization-community-1",
                    parent=self.window.root
                )
            )
            return

        # Iniciar captura de áudio
        # Nota: O pipeline processará o arquivo após a gravação, não em tempo real.
        # Para processamento em tempo real, precisaríamos de uma abordagem diferente (diart).
        self.audio_capture.start(sink_name, self.audio_file.name, self._audio_callback)
        self.recording = True
        logger.info("Gravação iniciada")

    def _audio_callback(self, chunk):
        """Called from audio capture with each audio chunk."""
        # Apenas armazenamos o áudio; o processamento será feito offline.
        pass

    def stop_recording(self):
        """Stop recording and begin offline processing with pyannote."""
        self.audio_capture.stop()
        self.recording = False
        logger.info("Gravação parada. Iniciando processamento com pyannote...")
        self.window.show_processing(True)
        threading.Thread(target=self._offline_processing, daemon=True).start()

    def _offline_processing(self):
        """Process the recorded audio with pyannote pipeline."""
        try:
            # Aplicar o pipeline ao arquivo gravado
            diarization = self.pipeline(self.audio_file.name)

            # A saída no pyannote 4.0 é um objeto DiarizationOutput
            # com atributos 'speaker_diarization' e 'exclusive_speaker_diarization' [citation:3][citation:5]
            result_text = "Resultado da diarização:\n"
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                result_text += f"{turn.start:.1f}s - {turn.end:.1f}s: {speaker}\n"

            # Atualizar a interface na thread principal
            self.window.root.after(0, self.window.display_transcript, result_text)

        except Exception as e:
            logger.error(f"Erro no processamento offline: {e}")
            self.window.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.window.root.after(0, self.window.show_processing, False)

    def on_step_end(self, step):
        """Placeholder para compatibilidade (não usado com pyannote puro)."""
        pass