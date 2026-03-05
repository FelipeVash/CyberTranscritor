# backend/deepseek_client.py
import json
import os
import requests
from pathlib import Path

CONFIG_PATH = Path.home() / ".deepseek_config.json"

class DeepSeekClient:
    BASE_URL = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self):
        self.api_key = self._load_or_request_key()

    def _load_or_request_key(self):
        """Carrega a chave do arquivo de configuração ou pede ao usuário."""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                return config.get("api_key")

        print("\n[DeepSeek] Para usar a IA, você precisa de uma chave de API.")
        print("Obtenha sua chave em: https://platform.deepseek.com/api_keys")
        api_key = input("Cole sua chave DeepSeek: ").strip()
        if not api_key:
            raise ValueError("Chave não fornecida.")
        with open(CONFIG_PATH, "w") as f:
            json.dump({"api_key": api_key}, f)
        os.chmod(CONFIG_PATH, 0o600)
        print("✅ Chave salva em ~/.deepseek_config.json (acesso restrito).")
        return api_key

    def ask(self, prompt, system_prompt="Você é um assistente útil e conciso.", 
            opt_out=True, enable_thinking=False, enable_web_search=False):
        """
        Envia uma pergunta para a DeepSeek e retorna a resposta.
        
        Args:
            prompt: texto do usuário
            system_prompt: instruções para o sistema
            opt_out: se True, inclui header para não usar dados no treinamento
            enable_thinking: se True, usa o modelo de raciocínio (deepseek-reasoner)
            enable_web_search: se True, permite busca na internet (se suportado)
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        if opt_out:
            headers["X-DS-OPT-OUT"] = "training"

        model = "deepseek-reasoner" if enable_thinking else "deepseek-chat"
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        
        if enable_web_search:
            data["enable_search"] = True

        try:
            response = requests.post(self.BASE_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            return f"Erro na API: {e}"
        except (KeyError, ValueError) as e:
            return f"Erro ao interpretar resposta: {e}"