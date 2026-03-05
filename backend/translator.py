# backend/translator.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import FLORES_CODES

class Translator:
    def __init__(self, source_lang="pt", target_lang="en", device=None):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.device = torch.device("cuda:0" if device == "cuda" and torch.cuda.is_available() else "cpu")
        self.model_name = "tencent/Hunyuan-MT-7B"
        print(f"Carregando Hunyuan-MT-7B ({source_lang} -> {target_lang})...")

        # Verifica se os códigos FLORES existem
        if source_lang not in FLORES_CODES:
            raise ValueError(f"Idioma de origem não suportado: {source_lang}")
        if target_lang not in FLORES_CODES:
            raise ValueError(f"Idioma de destino não suportado: {target_lang}")

        # Carrega tokenizer com src_lang
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto" if torch.cuda.is_available() else None
        )
        if not torch.cuda.is_available():
            self.model = self.model.to(self.device)

        # Template usado pelo Hunyuan-MT para tradução
        self.prompt_template = (
            "Translate the following segment from {source_lang} to {target_lang}, "
            "without additional explanation.\n\n{text}"
        )
        print("Modelo Hunyuan carregado.")

    def translate(self, text):
        if not text.strip():
            return ""
        try:
            prompt = self.prompt_template.format(
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                text=text
            )
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    num_beams=5,
                    early_stopping=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            generated = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            return generated.strip()
        except Exception as e:
            print(f"Erro na tradução Hunyuan: {e}")
            return f"[Erro: {e}]"

    def unload(self):
        """Descarrega o modelo da GPU para liberar memória."""
        if hasattr(self, 'model'):
            print("Descarregando modelo Hunyuan da GPU...")
            self.model.cpu()
            del self.model
            self.model = None
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
            self.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()