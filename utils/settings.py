# utils/settings.py
import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".transcritor_config.json"

DEFAULT_CONFIG = {
    "model_size": "tiny",
    "device": "cuda",
    "current_language": "pt",
    "translate_target": "en",
    "deepseek_model": "deepseek-chat"
}

def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                # garantir que todas as chaves existam
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    # opcional: restringir permissões
    os.chmod(CONFIG_PATH, 0o600)