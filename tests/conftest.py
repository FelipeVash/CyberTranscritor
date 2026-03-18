# tests/conftest.py
import sys
from unittest.mock import MagicMock, patch
import pytest
from pathlib import Path
import tempfile
import json
import logging
import time
import gc
import threading

# ============================================================================
# Global mocks for problematic modules that might create threads or access hardware
# ============================================================================

# Mock sounddevice to prevent real audio hardware access
mock_sounddevice = MagicMock()
mock_sounddevice.InputStream = MagicMock()
mock_sounddevice._terminate = MagicMock()

# Configure InputStream mock to return a tuple (audio_data, overflow_flag)
# to avoid "ValueError: not enough values to unpack" in recorder thread
mock_stream = MagicMock()
mock_stream.read.return_value = ([], False)
mock_sounddevice.InputStream.return_value = mock_stream

sys.modules['sounddevice'] = mock_sounddevice

# Mock piper and piper_tts to prevent loading real models
mock_piper = MagicMock()
sys.modules['piper'] = mock_piper
sys.modules['piper_tts'] = mock_piper

# Note: torch is NOT mocked globally, as it is needed for transformers import checks.
# It will be imported normally. We'll mock specific torch components in tests if needed.

# ============================================================================
# Now import application modules (safe after mocks)
# ============================================================================
from core.utils.logger import logger as app_logger
from core.utils.config_persistence import CONFIG_FILE
from core.controller.app_controller import AppController
import tkinter as tk

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def cleanup_resources():
    """
    Clean up resources after all tests to prevent leaks and SIGSEGV.
    With sounddevice mocked, no real threads should exist, but we keep as safety.
    """
    yield
    time.sleep(0.1)
    gc.collect()

@pytest.fixture(scope="session", autouse=True)
def configure_app_logging():
    """
    Add a FileHandler to the application logger to capture all logs
    during tests into logs/test_output.log.
    The handler is removed at the end of the session.
    """
    root_dir = Path(__file__).parent.parent
    log_dir = root_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "test_output.log"

    logger = app_logger

    # Avoid duplicate handlers
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file)
               for h in logger.handlers):
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Optional console handler for INFO level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        yield

        logger.removeHandler(file_handler)
        logger.removeHandler(console_handler)
        file_handler.close()
        console_handler.close()
    else:
        yield

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
    """
    Return an AppController with all external services mocked.
    The controller's Tkinter root is also mocked to avoid GUI creation.
    """
    # Remove real config file to prevent side effects
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

    with patch('core.controller.app_controller.ModelManager'), \
         patch('core.controller.app_controller.DeepSeekClient') as MockDeepSeek, \
         patch('core.controller.app_controller.AudioPlayer'), \
         patch('core.controller.app_controller.DBusService'):

        mock_deepseek = MagicMock()
        MockDeepSeek.return_value = mock_deepseek

        controller = AppController()
        core.controller._root = MagicMock()  # mock root to avoid Tk

        # Mock UI references
        core.controller.text_area = MagicMock()
        core.controller.trans_area = MagicMock()
        core.controller.btn_record = MagicMock()
        core.controller.btn_deepseek = MagicMock()
        core.controller.rec_indicator = MagicMock()
        core.controller.status_var = MagicMock()
        core.controller.progress_bar = MagicMock()

        # Mock Tkinter variables
        core.controller.model_size = MagicMock()
        core.controller.device = MagicMock()
        core.controller.current_language = MagicMock()
        core.controller.translate_target = MagicMock()
        core.controller.ui_language = MagicMock()
        core.controller.tts_voice = MagicMock()
        core.controller.translation_model = MagicMock()
        core.controller.idle_timeout = MagicMock()

        # Default return values (serializable)
        core.controller.current_language.get.return_value = "pt"
        core.controller.model_size.get.return_value = "tiny"
        core.controller.translate_target.get.return_value = "en"
        core.controller.tts_voice.get.return_value = "pt_BR-faber-medium"
        core.controller.device.get.return_value = "cuda"
        core.controller.ui_language.get.return_value = "English (en)"
        core.controller.translation_model.get.return_value = "nllb-3.3B"
        core.controller.idle_timeout.get.return_value = "60"

        # Mock service methods
        core.controller.show_info = MagicMock()
        core.controller.start_progress = MagicMock()
        core.controller.stop_progress = MagicMock()
        core.controller.translation_service = MagicMock()
        core.controller.translation_service.clear_cache = MagicMock()
        core.controller.translation_service.cache_stats = MagicMock(return_value={"size": 0, "max_size": 1000, "hits": 0, "misses": 0})

        return controller

@pytest.fixture
def mock_root():
    """Return a mock Tkinter root window."""
    root = MagicMock(spec=tk.Tk)
    root.winfo_exists.return_value = True
    return root