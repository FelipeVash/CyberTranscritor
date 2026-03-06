# utils/config_persistence.py
"""
Configuration persistence module.
Handles loading and saving user settings to a JSON file.
All logging is done through the centralized logger.
"""

import json
from pathlib import Path
from utils.logger import logger

CONFIG_FILE = Path.home() / ".transcritor_config.json"

def load_config():
    """
    Load saved configuration, or return default values if file doesn't exist.

    Returns:
        Dictionary with configuration keys and values.
    """
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
                # Update default with saved values (preserve any new keys)
                default.update(saved)
                logger.debug(f"Configuration loaded from {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    else:
        logger.debug("No configuration file found, using defaults")

    return default

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