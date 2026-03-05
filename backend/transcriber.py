# backend/transcriber.py
import torch
from transformers import pipeline
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

class TranscriberGPU:
    def __init__(self, model_size=None, device=None):
        self.model_size = model_size or config.MODEL_SIZE
        if (device or config.DEVICE) == "cuda" and torch.cuda.is_available():
            self.device = 0
            self.device_name = "cuda"
        else:
            self.device = -1
            self.device_name = "cpu"
        print(f"Carregando modelo whisper-{self.model_size} no dispositivo {self.device_name.upper()}...")
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=f"openai/whisper-{self.model_size}",
            device=self.device
        )
        print("Modelo carregado.")

    def transcribe(self, audio, language=None):
        """Transcreve um áudio (numpy array)."""
        if audio is None or len(audio) == 0:
            print("❌ Erro: áudio vazio ou inválido")
            return ""
        print(f"🎤 Transcrevendo áudio de {len(audio)} amostras...")
        generate_kwargs = {}
        if language:
            generate_kwargs["language"] = language
        try:
            result = self.pipe(audio, generate_kwargs=generate_kwargs)
            texto = result['text']
            print(f"📝 Transcrição: {texto[:50]}...")
            return texto
        except Exception as e:
            print(f"❌ Erro na transcrição: {e}")
            return f"[Erro: {e}]"

    def transcribe_file(self, audio_path, language=None):
        """Transcreve um arquivo de áudio."""
        generate_kwargs = {}
        if language:
            generate_kwargs["language"] = language
        result = self.pipe(audio_path, generate_kwargs=generate_kwargs)
        return result['text']