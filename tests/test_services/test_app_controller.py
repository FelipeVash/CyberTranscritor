# tests/test_services/test_app_controller.py
from unittest.mock import MagicMock, patch
import pytest
import tkinter as tk
from controller.app_controller import AppController
from utils.config_persistence import CONFIG_FILE

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
        mock_root.after = MagicMock()  # Ensure after is a mock method
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

        return controller

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
    mock_controller.translation_service = MagicMock()
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
    mock_controller.translation_service = MagicMock()
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
    with patch('sys.exit') as mock_exit:
        mock_controller.quit_app()
        mock_controller.model_manager.unload_all.assert_called_once()
        mock_exit.assert_called_once_with(0)