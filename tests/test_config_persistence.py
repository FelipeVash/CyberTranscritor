# tests/test_config_persistence.py
import json
from pathlib import Path
from core.utils.config_persistence import load_config, save_config, CONFIG_FILE, DEFAULT_CONFIG

def test_load_config_returns_defaults_when_file_not_exists(tmp_path, monkeypatch):
    monkeypatch.setattr('core.utils.config_persistence.CONFIG_FILE', tmp_path / "nonexistent.json")
    config = load_config()
    assert config == DEFAULT_CONFIG

def test_save_and_load_config(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    monkeypatch.setattr('core.utils.config_persistence.CONFIG_FILE', config_file)
    test_config = {"model_size": "tiny", "device": "cpu"}
    save_config(test_config)
    assert config_file.exists()
    loaded = load_config()
    # load_config mescla com defaults, então deve ter todas as chaves
    assert loaded["model_size"] == "tiny"
    assert loaded["device"] == "cpu"
    assert "source_language" in loaded  # do DEFAULT_CONFIG