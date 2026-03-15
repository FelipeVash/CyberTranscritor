# backend/transcriber.py
import torch
from transformers import pipeline
import numpy as np
import sys
from pathlib import Path
import warnings
sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from utils.logger import logger

warnings.filterwarnings("ignore", message=".*does not have many workers.*")
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

class TranscriberGPU:
    def __init__(self, model_size=None, device=None):
        self.model_size = model_size or config.MODEL_SIZE
        if (device or config.DEVICE) == "cuda" and torch.cuda.is_available():
            self.device = 0
            self.device_name = "cuda"
            self.torch_dtype = torch.float16
        else:
            self.device = -1
            self.device_name = "cpu"
            self.torch_dtype = torch.float32

        logger.info(f"Loading Whisper-{self.model_size} on {self.device_name.upper()} "
                    f"with dtype={self.torch_dtype}")
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=f"openai/whisper-{self.model_size}",
            device=self.device,
            model_kwargs={"torch_dtype": self.torch_dtype}
        )
        logger.info("Model loaded successfully")

    def transcribe(self, audio, language=None):
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
        logger.debug(f"Transcribing file: {audio_path}")
        generate_kwargs = {}
        if language:
            generate_kwargs["language"] = language
        result = self.pipe(audio_path, generate_kwargs=generate_kwargs)
        return result['text']

    def unload(self):
        """Unload the model from GPU to free memory."""
        logger.info("Unloading Whisper model from GPU")
        if hasattr(self, 'pipe') and self.pipe is not None:
            if hasattr(self.pipe, 'model'):
                try:
                    self.pipe.model.cpu()
                except:
                    pass
            del self.pipe
            self.pipe = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.debug("Whisper model unloaded")