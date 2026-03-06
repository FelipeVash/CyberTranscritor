# backend/translator.py
"""
Translation module using Meta's NLLB-200-3.3B model.
Executes 100% locally with GPU support.
All logging is done through the centralized logger.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import FLORES_CODES
from utils.logger import logger

class Translator:
    """
    Translator using the NLLB-200-3.3B model from Meta.
    Supports GPU acceleration (CUDA/ROCm) and CPU fallback.
    """

    def __init__(self, source_lang="pt", target_lang="en", device=None):
        """
        Initialize the translator and load the model.

        Args:
            source_lang: Source language code (e.g., 'pt')
            target_lang: Target language code (e.g., 'en')
            device: 'cuda' or 'cpu' (if 'cuda' not available, falls back to cpu)
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.device = torch.device("cuda:0" if device == "cuda" and torch.cuda.is_available() else "cpu")
        self.model_name = "facebook/nllb-200-3.3B"
        logger.info(f"Loading NLLB-200-3.3B ({source_lang} -> {target_lang})...")

        # Check if source and target languages are supported
        if source_lang not in FLORES_CODES:
            raise ValueError(f"Unsupported source language: {source_lang}")
        if target_lang not in FLORES_CODES:
            raise ValueError(f"Unsupported target language: {target_lang}")

        # Load tokenizer with source language
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            src_lang=FLORES_CODES[source_lang]
        )

        # Load model with optimizations for GPU
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
            device_map="auto" if self.device.type == "cuda" else None,
            low_cpu_mem_usage=True
        )

        if self.device.type == "cpu":
            self.model = self.model.to(self.device)

        logger.info("NLLB model loaded successfully")

    def translate(self, text):
        """
        Translate text from source_lang to target_lang.

        Args:
            text: String to be translated

        Returns:
            Translated string, or error message prefixed with "[Error:]"
        """
        if not text.strip():
            return ""

        try:
            # Tokenize input text
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)

            # Force the target language in the decoder
            forced_bos_token_id = self.tokenizer.lang_code_to_id[FLORES_CODES[self.target_lang]]

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    forced_bos_token_id=forced_bos_token_id,
                    max_new_tokens=512,
                    num_beams=5,
                    early_stopping=True,
                    no_repeat_ngram_size=3
                )

            translated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.debug(f"Translation ({self.source_lang}->{self.target_lang}): {translated[:50]}...")
            return translated.strip()

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return f"[Error: {e}]"

    def unload(self):
        """Unload the model from GPU to free memory."""
        if hasattr(self, 'model') and self.model is not None:
            logger.info("Unloading NLLB model from GPU")
            self.model.cpu()
            del self.model
            self.model = None
        if hasattr(self, 'tokenizer') and self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()