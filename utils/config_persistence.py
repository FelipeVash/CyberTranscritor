# utils/config_persistence.py
import json
from pathlib import Path
import config

CONFIG_FILE = Path.home() / ".transcritor_config.json"

def load_config():
    default = {
        "model_size": "tiny",
        "device": "cuda",
        "source_language": "pt",
        "target_language": "en",
        "language": config.LANGUAGE  # idioma da interface
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                default.update(saved)
        except Exception:
            pass
    return default

def save_config(config_dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_dict, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")