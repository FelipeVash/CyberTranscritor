# tests/test_services/test_app_controller.py
from unittest.mock import MagicMock, patch, call
import pytest
import tkinter as tk
from controller.app_controller import AppController
from core.utils.config_persistence import CONFIG_FILE

@pytest.fixture
def mock_controller():
    """Fixture that creates an AppController with mocks."""
    # Ensure config file doesn't exist to avoid real interactions
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

    with patch('controller.app_controller.ModelManager'), \
         patch('controller.app_controller.DeepSeekClient') as MockDeepSeek, \
         patch('controller.app_controller.AudioPlayer'), \
         patch('controller.app_controller.DBusService'):

        mock_deepseek = MagicMock()
        MockDeepSeek.return_value = mock_deepseek

        # Create controller
        controller = AppController()

        # Mock root with after method
        mock_root = MagicMock()
        mock_root.after = MagicMock()
        controller._root = mock_root

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

# ===== Existing tests =====
def test_controller_initialization(mock_controller):
    """Test if controller initializes correctly."""
    assert mock_controller is not None
    assert mock_controller.dbus_service is not None  # DBus is enabled by default
    assert mock_controller.deepseek_client is not None

def test_toggle_recording(mock_controller):
    """Test toggle_recording method."""
    mock_controller._toggle_recording_action = MagicMock()
    mock_controller.toggle_recording()
    mock_controller._toggle_recording_action.assert_called_once()

def test_start_recording(mock_controller):
    """Test start_recording method."""
    with patch('core.backend.audio.recorder.AudioRecorder') as MockRecorder:
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
    """Test stop_and_transcribe method."""
    # Configure a mock recorder
    mock_controller.recorder = MagicMock()
    mock_controller.recorder.stop.return_value = MagicMock(size=100)
    mock_controller.is_recording = True

    # Mock threading to avoid actual execution
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

def test_clear_translations(mock_controller):
    """Test clear_translations method."""
    mock_controller.clear_translations()
    mock_controller.trans_area.delete.assert_called_once_with(1.0, tk.END)

def test_translate_text(mock_controller):
    """Test translate_text method."""
    # Setup
    mock_controller.text_area.get.return_value = "Hello"
    mock_controller.translate_target.get.return_value = "pt"
    mock_controller.current_language.get.return_value = "en"

    # Mock translation service
    mock_controller.translation_service.translate.return_value = "Olá"

    # Mock threading to capture the target function
    with patch('threading.Thread') as MockThread:
        mock_thread = MagicMock()
        MockThread.return_value = mock_thread

        mock_controller.translate_text()

        # Verify progress started
        mock_controller.start_progress.assert_called_once()

        # Get the target function and call it (simulate background thread)
        args, kwargs = MockThread.call_args
        target_func = args[0] if args else kwargs.get('target')
        target_func()  # Execute the translation task

        # Verify translation service was called
        mock_controller.translation_service.translate.assert_called_with(
            "Hello",
            source_lang="en",
            target_lang="pt"
        )

        # Verify after callbacks were scheduled (root.after called)
        assert mock_controller._root.after.call_count >= 1

def test_translate_all(mock_controller):
    """Test translate_all method."""
    # Setup
    mock_controller.text_area.get.return_value = "Hello"
    mock_controller.current_language.get.return_value = "en"
    mock_controller.all_languages = ["pt", "en", "es", "fr"]  # Include source to test filtering

    # Mock translation service
    mock_controller.translation_service.translate.side_effect = ["Olá", "Hola", "Bonjour"]

    # Mock threading
    with patch('threading.Thread') as MockThread:
        mock_thread = MagicMock()
        MockThread.return_value = mock_thread

        mock_controller.translate_all()

        # Get the target function
        args, kwargs = MockThread.call_args
        target_func = args[0] if args else kwargs.get('target')
        target_func()  # Execute the multi-translation task

        # Verify translations for each target language (excluding source)
        assert mock_controller.translation_service.translate.call_count == 3
        mock_controller.translation_service.translate.assert_any_call("Hello", source_lang="en", target_lang="pt")
        mock_controller.translation_service.translate.assert_any_call("Hello", source_lang="en", target_lang="es")
        mock_controller.translation_service.translate.assert_any_call("Hello", source_lang="en", target_lang="fr")

        # Verify after callbacks were scheduled
        assert mock_controller._root.after.call_count >= 3

def test_insert_translation(mock_controller):
    """Test insert_translation method."""
    from datetime import datetime
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "12:34:56"

        mock_controller.insert_translation("pt", "Olá mundo")

        mock_controller.trans_area.insert.assert_any_call(tk.END, "[12:34:56] [PT] ")
        mock_controller.trans_area.insert.assert_any_call(tk.END, "Olá mundo\n\n")
        mock_controller.trans_area.see.assert_called_with(tk.END)

def test_quit_app(mock_controller):
    """Test the quit_app method."""
    with patch('sys.exit') as mock_exit, \
         patch('controller.app_controller.save_config') as mock_save:   # <-- adicionado
        mock_controller.quit_app()
        mock_controller.model_manager.unload_all.assert_called_once()
        mock_save.assert_called_once()                                   # <-- verifica chamada
        mock_exit.assert_called_once_with(0)

# ===== DeepSeek Window tests =====
def test_open_deepseek_window(mock_controller):
    """Test opening DeepSeek window when it doesn't exist."""
    mock_controller.deepseek_window = None
    with patch('controller.app_controller.DeepSeekWindow') as MockWindow:
        mock_window_instance = MagicMock()
        MockWindow.return_value = mock_window_instance

        mock_controller.open_deepseek_window()

        MockWindow.assert_called_once_with(
            mock_controller.root,
            mock_controller,
            audio_player=mock_controller.audio_player
        )
        assert mock_controller.deepseek_window == mock_window_instance

def test_open_deepseek_window_already_exists(mock_controller):
    """Test opening DeepSeek window when it already exists."""
    mock_window = MagicMock()
    mock_window.window.winfo_exists.return_value = True
    mock_controller.deepseek_window = mock_window

    with patch('controller.app_controller.DeepSeekWindow') as MockWindow:
        mock_controller.open_deepseek_window()

        MockWindow.assert_not_called()
        mock_window.show_window.assert_called_once()

def test_open_deepseek_window_error(mock_controller):
    """Test error handling when creating DeepSeek window."""
    mock_controller.deepseek_window = None
    mock_controller._handle_service_error = MagicMock()
    with patch('controller.app_controller.DeepSeekWindow') as MockWindow:
        MockWindow.side_effect = Exception("Creation failed")
        mock_controller.open_deepseek_window()

        mock_controller._handle_service_error.assert_called_once()
        # Verify the error message key is used
        args, kwargs = mock_controller._handle_service_error.call_args
        assert args[1] == "deepseek_window.messages.deepseek_error"

def test_open_deepseek_with_context(mock_controller):
    """Test opening DeepSeek window with initial prompt and response."""
    mock_controller.deepseek_window = None
    with patch('controller.app_controller.DeepSeekWindow') as MockWindow:
        mock_window_instance = MagicMock()
        MockWindow.return_value = mock_window_instance

        mock_controller.open_deepseek_with_context("prompt", "response")

        MockWindow.assert_called_once_with(
            mock_controller.root,
            mock_controller,
            initial_prompt="prompt",
            initial_response="response",
            audio_player=mock_controller.audio_player
        )

def test_open_deepseek_with_context_closes_existing(mock_controller):
    """Test opening with context closes existing window."""
    existing = MagicMock()
    existing.window.winfo_exists.return_value = True
    mock_controller.deepseek_window = existing

    with patch('controller.app_controller.DeepSeekWindow') as MockWindow:
        mock_window_instance = MagicMock()
        MockWindow.return_value = mock_window_instance

        mock_controller.open_deepseek_with_context("prompt", "response")

        existing.destroy.assert_called_once()
        MockWindow.assert_called_once()

def test_open_deepseek_with_context_error(mock_controller):
    """Test error handling when opening with context."""
    mock_controller.deepseek_window = None
    mock_controller._handle_service_error = MagicMock()
    with patch('controller.app_controller.DeepSeekWindow') as MockWindow:
        MockWindow.side_effect = Exception("Context error")

        mock_controller.open_deepseek_with_context("prompt", "response")

        mock_controller._handle_service_error.assert_called_once()
        # No specific error key, just the exception
        args, kwargs = mock_controller._handle_service_error.call_args
        assert isinstance(args[0], Exception)

def test_stop_all_audio(mock_controller):
    """Test stop_all_audio method."""
    mock_controller.audio_player.stop = MagicMock()
    mock_controller.stop_all_audio()
    mock_controller.audio_player.stop.assert_called_once()