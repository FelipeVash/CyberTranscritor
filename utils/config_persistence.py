# utils/config_persistence.py
import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".transcritor_config.json"

def load_config():
    """Carrega as configurações salvas, ou retorna valores padrão."""
    default = {
        "model_size": "tiny",
        "device": "cuda",
        "source_language": "pt",
        "target_language": "en"
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                # Atualiza o default com os valores salvos (preserva chaves novas)
                default.update(saved)
        except Exception:
            pass
    return default

def save_config(config_dict):
    """Salva as configurações em JSON."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_dict, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")