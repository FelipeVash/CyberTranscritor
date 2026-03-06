# backend/translator.py
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import FLORES_CODES

class Translator:
    """
    Tradutor usando modelo NLLB-200-3.3B da Meta.
    Execução 100% local com suporte a GPU.
    """
    def __init__(self, source_lang="pt", target_lang="en", device=None):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.device = torch.device("cuda:0" if device == "cuda" and torch.cuda.is_available() else "cpu")
        self.model_name = "facebook/nllb-200-3.3B"
        print(f"Carregando NLLB-200-3.3B ({source_lang} -> {target_lang})...")

        # Verifica se os códigos FLORES existem
        if source_lang not in FLORES_CODES:
            raise ValueError(f"Idioma de origem não suportado: {source_lang}")
        if target_lang not in FLORES_CODES:
            raise ValueError(f"Idioma de destino não suportado: {target_lang}")

        # Carrega tokenizer com idioma de origem
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            src_lang=FLORES_CODES[source_lang]
        )

        # Carrega modelo com configuração otimizada para GPU
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
            device_map="auto" if self.device.type == "cuda" else None,
            low_cpu_mem_usage=True
        )

        if self.device.type == "cpu":
            self.model = self.model.to(self.device)

        print("Modelo NLLB carregado com sucesso.")

    def translate(self, text):
        """Traduz o texto de source_lang para target_lang."""
        if not text.strip():
            return ""

        try:
            # Tokeniza o texto de entrada
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)

            # Define o token de início do decoder para o idioma de destino
            forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(FLORES_CODES[self.target_lang])

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
            return translated.strip()

        except Exception as e:
            print(f"Erro na tradução NLLB: {e}")
            return f"[Erro: {e}]"

    def unload(self):
        """Descarrega o modelo da GPU para liberar memória."""
        if hasattr(self, 'model') and self.model is not None:
            print("Descarregando NLLB da GPU...")
            self.model.cpu()
            del self.model
            self.model = None
        if hasattr(self, 'tokenizer') and self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()