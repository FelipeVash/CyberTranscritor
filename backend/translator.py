"""
Translation module using Meta's NLLB-200 models.
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
    Translator using NLLB models from Meta.
    Supports different model sizes and GPU acceleration (CUDA/ROCm).
    """

    # Mapping from our model size keys to Hugging Face model IDs
    MODEL_MAP = {
        "nllb-200M": "facebook/nllb-200-distilled-600M",   # actually 600M, but it's the smallest distilled
        "nllb-600M": "facebook/nllb-200-distilled-600M",
        "nllb-1.3B": "facebook/nllb-200-1.3B",
        "nllb-3.3B": "facebook/nllb-200-3.3B"
    }

    def __init__(self, source_lang="pt", target_lang="en", model_size="nllb-3.3B", device=None):
        """
        Initialize the translator and load the model.

        Args:
            source_lang: Source language code (e.g., 'pt')
            target_lang: Target language code (e.g., 'en')
            model_size: Size of the NLLB model (e.g., 'nllb-200M', 'nllb-3.3B')
            device: 'cuda' or 'cpu' (if 'cuda' not available, falls back to cpu)
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.model_size = model_size

        # Determine device
        if device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda:0")
            self.device_name = "cuda"
        else:
            self.device = torch.device("cpu")
            self.device_name = "cpu"

        # Get actual model name from map
        self.model_name = self.MODEL_MAP.get(model_size, "facebook/nllb-200-3.3B")
        logger.info(f"Loading {self.model_name} ({source_lang} -> {target_lang})...")

        # Check if source and target languages are supported
        if source_lang not in FLORES_CODES:
            raise ValueError(f"Unsupported source language: {source_lang}. Supported: {', '.join(FLORES_CODES.keys())}")
        if target_lang not in FLORES_CODES:
            raise ValueError(f"Unsupported target language: {target_lang}. Supported: {', '.join(FLORES_CODES.keys())}")

        # Load tokenizer with source language
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            src_lang=FLORES_CODES[source_lang]
        )

        # Load model with appropriate dtype
        torch_dtype = torch.float16 if self.device.type == "cuda" else torch.float32
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True
        )
        self.model = self.model.to(self.device)

        logger.info(f"NLLB model loaded successfully on {self.device_name}")

    def _get_forced_bos_token_id(self):
        """Get the forced BOS token ID for the target language."""
        target_flores = FLORES_CODES[self.target_lang]
        token_str = f"__{target_flores}__"

        # Try to get the ID directly
        token_id = self.tokenizer.convert_tokens_to_ids(token_str)

        # If it's the unknown token, search vocabulary for any token containing the FLORES code
        if token_id == self.tokenizer.unk_token_id:
            vocab = self.tokenizer.get_vocab()
            for t, idx in vocab.items():
                if target_flores in t:
                    token_id = idx
                    logger.debug(f"Found token '{t}' with id {idx} for language {self.target_lang}")
                    break
            else:
                raise RuntimeError(f"Token for language {self.target_lang} ({target_flores}) not found in vocabulary")

        logger.debug(f"Forced BOS token ID for {self.target_lang}: {token_id}")
        return token_id

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
            )
            # Move inputs to the same device as the model
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Convert inputs to the model's dtype (if model is half, inputs should be half)
            model_dtype = next(self.model.parameters()).dtype
            if model_dtype == torch.float16:
                inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}

            # Force the target language in the decoder
            forced_bos_token_id = self._get_forced_bos_token_id()

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

            # Ensure string is clean UTF-8
            if isinstance(translated, bytes):
                translated = translated.decode('utf-8', errors='ignore')
            else:
                translated = str(translated).encode('utf-8', errors='ignore').decode('utf-8')

            logger.debug(f"Translation ({self.source_lang}->{self.target_lang}): {translated[:50]}...")
            return translated.strip()

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return f"[Error: {e}]"

    def unload(self):
        """Unload the model from GPU to free memory."""
        if hasattr(self, 'model') and self.model is not None:
            logger.info(f"Unloading NLLB model {self.model_size} from {self.device_name}")
            self.model.cpu()
            del self.model
            self.model = None
        if hasattr(self, 'tokenizer') and self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        if self.device.type == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()