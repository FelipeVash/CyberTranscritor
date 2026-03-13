# tests/test_services/test_app_controller.py
from unittest.mock import MagicMock, patch
import pytest
from controller.app_controller import AppController
from utils.config_persistence import CONFIG_FILE

@pytest.fixture
def mock_controller():
    """Fixture que cria um AppController com D-Bus desabilitado e DeepSeek mockado."""
    # Garante que o arquivo de configuração não exista para evitar interações reais
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

    # Mock do DeepSeekClient para evitar input() nos testes
    with patch('controller.app_controller.DeepSeekClient') as MockDeepSeek:
        mock_deepseek = MagicMock()
        MockDeepSeek.return_value = mock_deepseek

        # Cria o controller com D-Bus desabilitado
        controller = AppController(enable_dbus=False)

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

        # Mock dos métodos que serão verificados nos testes
        controller.show_info = MagicMock()
        controller.start_progress = MagicMock()
        controller.stop_progress = MagicMock()

        # Mock do translation_service e seus métodos
        controller.translation_service = MagicMock()
        controller.translation_service.clear_cache = MagicMock()
        controller.translation_service.cache_stats = MagicMock(return_value={"size": 0, "max_size": 1000, "hits": 0, "misses": 0})

        yield controller

def test_controller_initialization(mock_controller):
    """Testa se o controller é inicializado corretamente."""
    assert mock_controller is not None
    assert mock_controller.dbus_service is None  # D-Bus desabilitado
    assert mock_controller.deepseek_client is not None  # Mockado

def test_clear_translation_cache(mock_controller):
    """Testa o método clear_translation_cache."""
    mock_controller.clear_translation_cache()
    mock_controller.translation_service.clear_cache.assert_called_once()
    mock_controller.show_info.assert_called_once()

def test_get_translation_cache_stats(mock_controller):
    """Testa o método get_translation_cache_stats."""
    stats = mock_controller.get_translation_cache_stats()
    assert stats == {"size": 0, "max_size": 1000, "hits": 0, "misses": 0}

def test_toggle_recording(mock_controller):
    """Testa o método toggle_recording."""
    mock_controller._toggle_recording_action = MagicMock()
    mock_controller.toggle_recording()
    mock_controller._toggle_recording_action.assert_called_once()

def test_start_recording(mock_controller):
    """Testa o método start_recording."""
    with patch('backend.audio.recorder.AudioRecorder') as MockRecorder:
        mock_recorder = MagicMock()
        MockRecorder.return_value = mock_recorder

        mock_controller.start_recording()

        assert mock_controller.is_recording is True
        mock_controller.text_area.delete.assert_called()
        mock_controller.trans_area.delete.assert_called()
        mock_controller.btn_record.config.assert_called()
        mock_controller.btn_deepseek.config.assert_called_with(state="disabled")
        mock_controller.rec_indicator.config.assert_called()
        mock_controller.status_var.set.assert_called()

def test_stop_and_transcribe(mock_controller):
    """Testa o método stop_and_transcribe."""
    # Configura um recorder mock
    mock_controller.recorder = MagicMock()
    mock_controller.recorder.stop.return_value = MagicMock(size=100)
    mock_controller.is_recording = True

    # Mock da thread para não executar de fato
    with patch('threading.Thread') as MockThread:
        mock_thread = MagicMock()
        MockThread.return_value = mock_thread

        mock_controller.stop_and_transcribe()

        assert mock_controller.is_recording is False
        mock_controller.btn_record.config.assert_called()
        mock_controller.rec_indicator.config.assert_called()
        mock_controller.status_var.set.assert_called()
        mock_controller.start_progress.assert_called_once()
        mock_thread.start.assert_called_once()