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
    """Cria um arquivo de configuração temporário e retorna seu caminho."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"test": True}, f)
        path = Path(f.name)
    yield path
    path.unlink()

@pytest.fixture
def mock_controller():
    """Retorna um AppController com mocks para evitar criação real de serviços."""
    with patch('controller.app_controller.ModelManager'), \
         patch('controller.app_controller.DeepSeekClient'), \
         patch('controller.app_controller.AudioPlayer'), \
         patch('controller.app_controller.DBusService'):
        controller = AppController()
        # Evita que o controller tente criar variáveis Tkinter (root não existe)
        controller._root = MagicMock()
        return controller

@pytest.fixture
def mock_root():
    """Retorna um mock da janela raiz Tkinter."""
    root = MagicMock(spec=tk.Tk)
    root.winfo_exists.return_value = True
    return root