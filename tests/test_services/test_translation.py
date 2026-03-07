# tests/test_services/test_translation.py
import pytest
from unittest.mock import MagicMock, patch
from backend.services.translation_service import TranslationService, TranslationError

@pytest.fixture
def mock_model_manager():
    mm = MagicMock()
    mm.get_translator.return_value.translate.return_value = "translated text"
    return mm

def test_translate_success(mock_model_manager):
    service = TranslationService(mock_model_manager)
    result = service.translate("Hello", source_lang="en", target_lang="pt")
    assert result == "translated text"
    mock_model_manager.get_translator.assert_called_with("en", "pt")

def test_translate_error_handling(mock_model_manager):
    mock_model_manager.get_translator.return_value.translate.side_effect = Exception("API error")
    service = TranslationService(mock_model_manager)
    with pytest.raises(TranslationError):
        service.translate("Hello", source_lang="en", target_lang="pt")