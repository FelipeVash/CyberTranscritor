# tests/test_services/test_app_controller.py
from unittest.mock import MagicMock, patch
import pytest
from controller.app_controller import AppController
from utils.config_persistence import CONFIG_FILE

@pytest.fixture
def mock_controller():
    # Garante que o arquivo de configuração não exista para evitar interações reais
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    # Cria o controller com D-Bus desabilitado
    controller = AppController(enable_dbus=True)
    # Mocks para atributos de UI
    controller.text_area = MagicMock()
    controller.trans_area = MagicMock()
    controller.btn_record = MagicMock()
    controller.btn_deepseek = MagicMock()
    controller.rec_indicator = MagicMock()
    controller.status_var = MagicMock()
    controller.progress_bar = MagicMock()
    # Mocks para variáveis Tkinter (StringVar)
    controller.model_size = MagicMock()
    controller.device = MagicMock()
    controller.current_language = MagicMock()
    controller.translate_target = MagicMock()
    controller.ui_language = MagicMock()
    controller.tts_voice = MagicMock()
    controller.translation_model = MagicMock()
    controller.idle_timeout = MagicMock()
    # Configura retornos padrão
    controller.current_language.get.return_value = "pt"
    controller.model_size.get.return_value = "tiny"
    controller.translate_target.get.return_value = "en"
    controller.tts_voice.get.return_value = "pt_BR-faber-medium"
    return controller