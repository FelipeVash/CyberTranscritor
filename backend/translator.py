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
            raise ValueError(f"Unsupported source language: {source_lang}. Supported: {', '.join(FLORES_CODES.keys())}")
        if target_lang not in FLORES_CODES:
            raise ValueError(f"Unsupported target language: {target_lang}. Supported: {', '.join(FLORES_CODES.keys())}")

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

        # Determine the correct attribute for language code mapping
        # Some versions use 'lang_code_to_id', others use 'converter'
        if hasattr(self.tokenizer, 'lang_code_to_id'):
            self.lang_code_attr = 'lang_code_to_id'
        elif hasattr(self.tokenizer, '_lang_code_to_id'):
            self.lang_code_attr = '_lang_code_to_id'
        elif hasattr(self.tokenizer, 'converter') and hasattr(self.tokenizer.converter, 'lang_code_to_id'):
            # For older versions where tokenizer has a converter
            self.lang_code_attr = 'converter.lang_code_to_id'
        else:
            # Fallback: try to access via tokenizer's vocab
            logger.warning("Could not find lang_code_to_id attribute. Attempting fallback.")
            self.lang_code_attr = None

        logger.info("NLLB model loaded successfully")

    def _get_forced_bos_token_id(self):
        """Get the forced BOS token ID for the target language."""
        target_flores = FLORES_CODES[self.target_lang]
        token_str = f"__{target_flores}__"
        
        # Tenta obter o ID diretamente
        token_id = self.tokenizer.convert_tokens_to_ids(token_str)
        
        # Se for o token desconhecido (unk_token_id), tenta buscar no vocabulário
        if token_id == self.tokenizer.unk_token_id:
            # Procura qualquer token que contenha o código FLORES
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
        forced_bos_token_id = self._get_forced_bos_token_id()
        logger.debug(f"Using forced_bos_token_id={forced_bos_token_id}")
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
            
            # Garantir que a string seja UTF-8 limpa
            if isinstance(translated, bytes):
                translated = translated.decode('utf-8', errors='ignore')
            else:
                # Forçar conversão para string e remover caracteres problemáticos
                translated = str(translated).encode('utf-8', errors='ignore').decode('utf-8')
            
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