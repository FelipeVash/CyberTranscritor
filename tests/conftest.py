# tests/conftest.py
import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import MagicMock, patch

from utils.logger import setup_logger
from utils.i18n import I18n
from utils.config_persistence import load_config, save_config, CONFIG_FILE
from controller.app_controller import AppController
import tkinter as tk

@pytest.fixture(scope="session")
def temp_config_file():
    """Create a temporary configuration file and return its path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"test": True}, f)
        path = Path(f.name)
    yield path
    path.unlink()

@pytest.fixture
def mock_controller():
    """Return an AppController with mocks to avoid real service creation."""
    # Ensure config file doesn't exist to avoid real interactions
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

    with patch('controller.app_controller.ModelManager'), \
         patch('controller.app_controller.DeepSeekClient') as MockDeepSeek, \
         patch('controller.app_controller.AudioPlayer'), \
         patch('controller.app_controller.DBusService'):
        
        mock_deepseek = MagicMock()
        MockDeepSeek.return_value = mock_deepseek
        controller = AppController()
        
        # Prevent controller from trying to create Tkinter variables (root doesn't exist)
        controller._root = MagicMock()
        
        # Mock UI references
        controller.text_area = MagicMock()
        controller.trans_area = MagicMock()
        controller.btn_record = MagicMock()
        controller.btn_deepseek = MagicMock()
        controller.rec_indicator = MagicMock()
        controller.status_var = MagicMock()
        controller.progress_bar = MagicMock()

        # Mock Tkinter variables
        controller.model_size = MagicMock()
        controller.device = MagicMock()
        controller.current_language = MagicMock()
        controller.translate_target = MagicMock()
        controller.ui_language = MagicMock()
        controller.tts_voice = MagicMock()
        controller.translation_model = MagicMock()
        controller.idle_timeout = MagicMock()

        # Default return values
        controller.current_language.get.return_value = "pt"
        controller.model_size.get.return_value = "tiny"
        controller.translate_target.get.return_value = "en"
        controller.tts_voice.get.return_value = "pt_BR-faber-medium"

        # Mock methods that will be checked in tests
        controller.show_info = MagicMock()
        controller.start_progress = MagicMock()
        controller.stop_progress = MagicMock()
        controller.translation_service = MagicMock()
        controller.translation_service.clear_cache = MagicMock()
        controller.translation_service.cache_stats = MagicMock(return_value={"size": 0, "max_size": 1000, "hits": 0, "misses": 0})

        return controller

@pytest.fixture
def mock_root():
    """Return a mock Tkinter root window."""
    root = MagicMock(spec=tk.Tk)
    root.winfo_exists.return_value = True
    return root