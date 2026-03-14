# tests/test_services/test_transcription.py
import pytest
from unittest.mock import MagicMock, patch
from backend.services.transcription_service import TranscriptionService, TranscriptionError

@pytest.fixture
def mock_model_manager():
    mm = MagicMock()
    mm.get_transcriber.return_value.transcribe.return_value = "transcribed text"
    return mm

def test_transcribe_success(mock_model_manager):
    service = TranscriptionService(mock_model_manager)
    result = service.transcribe(b"fake audio", language="pt", model_size="tiny")
    assert result == "transcribed text"
    # Use assert_called_with with keyword argument to match the actual call
    mock_model_manager.get_transcriber.assert_called_with(model_size="tiny")

def test_transcribe_error_handling(mock_model_manager):
    mock_model_manager.get_transcriber.return_value.transcribe.side_effect = Exception("API error")
    service = TranscriptionService(mock_model_manager)
    with pytest.raises(TranscriptionError):
        service.transcribe(b"fake audio")