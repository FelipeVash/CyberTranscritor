# backend/deepseek_client.py
"""
DeepSeek API client module.
Handles authentication and communication with the DeepSeek API.
All logging is done through the centralized logger.
"""

import json
import os
import requests
from pathlib import Path
from utils.logger import logger

CONFIG_PATH = Path.home() / ".deepseek_config.json"

class DeepSeekClient:
    """
    Client for the DeepSeek API.
    Reads the API key from ~/.deepseek_config.json.
    """

    BASE_URL = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self):
        """Initialize the client by loading the API key."""
        self.api_key = self._load_or_request_key()
        logger.info("DeepSeek client initialized")

    def _load_or_request_key(self):
        """
        Load the API key from the config file, or request it from the user if missing.
        The key is saved to ~/.deepseek_config.json with restricted permissions.
        """
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                    key = config.get("api_key")
                    if key:
                        logger.debug("API key loaded from config file")
                        return key
            except Exception as e:
                logger.error(f"Failed to read config file: {e}")

        # If we reach here, no valid key was found
        logger.warning("No API key found, prompting user")
        print("\n[DeepSeek] To use the AI, you need an API key.")
        print("Get your key at: https://platform.deepseek.com/api_keys")
        api_key = input("Paste your DeepSeek key: ").strip()
        if not api_key:
            raise ValueError("No API key provided.")
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump({"api_key": api_key}, f)
            os.chmod(CONFIG_PATH, 0o600)  # Restrict permissions
            logger.info(f"API key saved to {CONFIG_PATH} with restricted permissions")
        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
        return api_key

    def ask(self, prompt, system_prompt="You are a helpful and concise assistant.",
            opt_out=True, enable_thinking=False, enable_web_search=False):
        """
        Send a query to DeepSeek and return the response.

        Args:
            prompt: User's text
            system_prompt: System instructions
            opt_out: If True, include header to opt out of data training
            enable_thinking: If True, use the deepseek-reasoner model
            enable_web_search: If True, allow internet search (if supported)

        Returns:
            Response string, or error message prefixed with "[Error:]"
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
            logger.debug(f"Sending request to DeepSeek API (model={model})")
            response = requests.post(self.BASE_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.debug("Received response from DeepSeek")
            return content
        except requests.exceptions.Timeout:
            logger.error("DeepSeek API request timed out")
            return "[Error: Request timed out]"
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            return f"[Error: {e}]"
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse DeepSeek API response: {e}")
            return f"[Error: {e}]"