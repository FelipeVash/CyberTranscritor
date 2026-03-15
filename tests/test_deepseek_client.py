# tests/test_deepseek_client.py
"""
Tests for the DeepSeek API client.
"""

import json
import pytest
import requests  # <-- adicionado
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from backend.deepseek_client import DeepSeekClient, CONFIG_PATH

# Fixture to mock the config file path and avoid touching real user files
@pytest.fixture
def mock_config_path(tmp_path, monkeypatch):
    """Set CONFIG_PATH to a temporary location."""
    fake_path = tmp_path / ".deepseek_config.json"
    monkeypatch.setattr('backend.deepseek_client.CONFIG_PATH', fake_path)
    return fake_path

def test_load_key_from_existing_file(mock_config_path):
    """Test loading API key from existing config file."""
    mock_config_path.write_text(json.dumps({"api_key": "test-key-123"}))
    client = DeepSeekClient()
    assert client.api_key == "test-key-123"

def test_load_key_creates_file_when_missing(mock_config_path, monkeypatch):
    """Test that client prompts for key and creates file when missing."""
    monkeypatch.setattr('builtins.input', lambda _: "user-provided-key")
    if mock_config_path.exists():
        mock_config_path.unlink()
    monkeypatch.setattr('os.chmod', lambda path, mode: None)
    
    client = DeepSeekClient()
    assert client.api_key == "user-provided-key"
    assert mock_config_path.exists()
    data = json.loads(mock_config_path.read_text())
    assert data["api_key"] == "user-provided-key"

def test_load_key_raises_error_if_no_input(mock_config_path, monkeypatch):
    """Test that empty input raises ValueError."""
    monkeypatch.setattr('builtins.input', lambda _: "")
    if mock_config_path.exists():
        mock_config_path.unlink()
    with pytest.raises(ValueError, match="No API key provided"):
        DeepSeekClient()

def test_ask_success(monkeypatch):
    """Test successful API call."""
    client = DeepSeekClient()
    client.api_key = "test-key"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello, world!"}}]
    }
    with patch('requests.post', return_value=mock_response) as mock_post:
        result = client.ask("Hi", system_prompt="Be nice")
        assert result == "Hello, world!"
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        assert call_args['headers']['Authorization'] == "Bearer test-key"
        assert 'X-DS-OPT-OUT' in call_args['headers']
        assert call_args['json']['model'] == "deepseek-chat"
        assert call_args['json']['messages'][1]['content'] == "Hi"

def test_ask_with_thinking(monkeypatch):
    """Test enabling thinking (reasoner model)."""
    client = DeepSeekClient()
    client.api_key = "test-key"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"choices": [{"message": {"content": "Reasoned answer"}}]}
    with patch('requests.post', return_value=mock_response) as mock_post:
        result = client.ask("Why?", enable_thinking=True)
        assert result == "Reasoned answer"
        call_json = mock_post.call_args[1]['json']
        assert call_json['model'] == "deepseek-reasoner"

def test_ask_with_web_search(monkeypatch):
    """Test enabling web search."""
    client = DeepSeekClient()
    client.api_key = "test-key"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"choices": [{"message": {"content": "Search result"}}]}
    with patch('requests.post', return_value=mock_response) as mock_post:
        result = client.ask("Search something", enable_web_search=True)
        assert result == "Search result"
        call_json = mock_post.call_args[1]['json']
        assert call_json.get('enable_search') is True

def test_ask_timeout(monkeypatch):
    """Test timeout exception."""
    client = DeepSeekClient()
    client.api_key = "test-key"
    with patch('requests.post', side_effect=requests.exceptions.Timeout):
        result = client.ask("Hi")
        assert result.startswith("[Error: Request timed out]")

def test_ask_request_exception(monkeypatch):
    """Test general request exception."""
    client = DeepSeekClient()
    client.api_key = "test-key"
    with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Failed")):
        result = client.ask("Hi")
        assert result.startswith("[Error: Failed]")

def test_ask_invalid_response(monkeypatch):
    """Test malformed JSON response."""
    client = DeepSeekClient()
    client.api_key = "test-key"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("No JSON")
    with patch('requests.post', return_value=mock_response):
        result = client.ask("Hi")
        assert result.startswith("[Error: No JSON]")