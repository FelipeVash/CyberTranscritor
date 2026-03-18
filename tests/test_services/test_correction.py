# tests/test_services/test_correction.py
import pytest
from unittest.mock import patch, MagicMock
from core.backend.services.correction_service import CorrectionService, CorrectionError

def test_correct_success():
    with patch('core.backend.services.correction_service.correct_text', return_value="text corrected") as mock:
        service = CorrectionService()
        result = service.correct("text", "pt")
        assert result == "text corrected"
        mock.assert_called_with("text", "pt")

def test_correct_error_handling():
    with patch('core.backend.services.correction_service.correct_text', side_effect=Exception("fail")):
        service = CorrectionService()
        with pytest.raises(CorrectionError):
            service.correct("text", "pt")