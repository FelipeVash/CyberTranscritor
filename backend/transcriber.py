# backend/transcriber.py
"""
Audio transcription module using Whisper models via Hugging Face Transformers.
Supports GPU (CUDA/ROCm) and CPU.
All logging is done through the centralized logger.
"""

import torch
from transformers import pipeline
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from utils.logger import logger

class TranscriberGPU:
    """
    Whisper-based transcriber with GPU support.
    Loads the model once and reuses it for multiple transcriptions.
    """

    def __init__(self, model_size=None, device=None):
        """
        Initialize the transcriber and load the model.

        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            device: 'cuda' or 'cpu' (if 'cuda' not available, falls back to cpu)
        """
        self.model_size = model_size or config.MODEL_SIZE
        if (device or config.DEVICE) == "cuda" and torch.cuda.is_available():
            self.device = 0
            self.device_name = "cuda"
        else:
            self.device = -1
            self.device_name = "cpu"

        logger.info(f"Loading Whisper-{self.model_size} on {self.device_name.upper()}")
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=f"openai/whisper-{self.model_size}",
            device=self.device
        )
        logger.info("Model loaded successfully")

    def transcribe(self, audio, language=None):
        """
        Transcribe audio (numpy array) to text.

        Args:
            audio: numpy array of audio samples (expected at 16kHz)
            language: language code (e.g., 'pt') or None for auto-detection

        Returns:
            Transcribed text as string.
        """
        if audio is None or len(audio) == 0:
            logger.error("Empty or invalid audio input")
            return ""

        logger.debug(f"Transcribing audio of {len(audio)} samples")
        generate_kwargs = {}
        if language:
            generate_kwargs["language"] = language

        try:
            result = self.pipe(audio, generate_kwargs=generate_kwargs)
            text = result['text']
            logger.debug(f"Transcription result: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return f"[Error: {e}]"

    def transcribe_file(self, audio_path, language=None):
        """
        Transcribe an audio file.

        Args:
            audio_path: path to audio file
            language: language code or None

        Returns:
            Transcribed text.
        """
        logger.debug(f"Transcribing file: {audio_path}")
        generate_kwargs = {}
        if language:
            generate_kwargs["language"] = language
        result = self.pipe(audio_path, generate_kwargs=generate_kwargs)
        return result['text']