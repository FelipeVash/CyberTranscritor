# utils/config_persistence.py
"""
Configuration persistence module.
Handles loading and saving user settings to a JSON file.
All logging is done through the centralized logger.
"""

import json
from pathlib import Path
from core.utils.logger import logger

CONFIG_FILE = Path.home() / ".transcritor_config.json"

# Default configuration values
DEFAULT_CONFIG = {
    "model_size": "large",
    "device": "cuda",
    "source_language": "pt",
    "target_language": "en",
    "ui_language": "en",
    "tts_voice": "pt_BR-faber-medium",
    "translation_model": "nllb-3.3B",
    "idle_timeout": 60  # seconds
}

def load_config():
    """
    Load saved configuration, or return default values if file doesn't exist.

    Returns:
        Dictionary with configuration keys and values.
    """
    config = DEFAULT_CONFIG.copy()

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                # Update config with saved values, preserving defaults for missing keys
                config.update(saved)
                logger.debug(f"Configuration loaded from {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    else:
        logger.debug("No configuration file found, using defaults")

    return config

def save_config(config_dict):
    """
    Save configuration to JSON file.

    Args:
        config_dict: Dictionary with configuration keys and values.
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_dict, f, indent=2)
        logger.debug(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")