# tests/test_hardware_detector.py
import pytest
from unittest.mock import patch, MagicMock
from utils.hardware_detector import (
    detect_device, get_gpu_memory, recommend_whisper_model,
    recommend_translation_model, get_recommended_settings
)

def test_detect_device_no_gpu():
    with patch('torch.cuda.is_available', return_value=False):
        assert detect_device() == 'cpu'

def test_detect_device_with_gpu():
    with patch('torch.cuda.is_available', return_value=True):
        assert detect_device() == 'cuda'

def test_get_gpu_memory_rocm_success():
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "VRAM Total: 16384 MB\nVRAM Used: 1024 MB"
    with patch('subprocess.run', return_value=mock_run):
        mem = get_gpu_memory()
        assert mem == 16.0  # 16384/1024

def test_get_gpu_memory_nvidia_success():
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "8192"
    with patch('subprocess.run', return_value=mock_run):
        mem = get_gpu_memory()
        assert mem == 8.0

def test_get_gpu_memory_fallback_torch():
    with patch('subprocess.run', side_effect=FileNotFoundError()), \
         patch('torch.cuda.get_device_properties') as mock_prop:
        mock_prop.return_value.total_memory = 6 * 1024**3  # 6GB
        mem = get_gpu_memory()
        assert mem == 6.0

def test_recommend_whisper_model_cpu():
    with patch('utils.hardware_detector.get_ram_gb', return_value=8.0):
        assert recommend_whisper_model('cpu') == 'tiny'
    with patch('utils.hardware_detector.get_ram_gb', return_value=16.0):
        assert recommend_whisper_model('cpu') == 'base'

def test_recommend_whisper_model_gpu():
    assert recommend_whisper_model('cuda', gpu_mem=12.0) == 'large'
    assert recommend_whisper_model('cuda', gpu_mem=8.0) == 'medium'
    assert recommend_whisper_model('cuda', gpu_mem=4.0) == 'small'
    assert recommend_whisper_model('cuda', gpu_mem=2.0) == 'base'
    assert recommend_whisper_model('cuda', gpu_mem=1.0) == 'tiny'

def test_recommend_translation_model_cpu():
    assert recommend_translation_model('cpu') == 'nllb-200M'

def test_recommend_translation_model_gpu():
    assert recommend_translation_model('cuda', gpu_mem=12.0) == 'nllb-3.3B'
    assert recommend_translation_model('cuda', gpu_mem=7.0) == 'nllb-1.3B'
    assert recommend_translation_model('cuda', gpu_mem=4.0) == 'nllb-600M'
    assert recommend_translation_model('cuda', gpu_mem=2.0) == 'nllb-200M'

def test_get_recommended_settings():
    with patch('utils.hardware_detector.detect_device', return_value='cuda'), \
         patch('utils.hardware_detector.get_gpu_memory', return_value=8.0):
        settings = get_recommended_settings()
        assert settings['device'] == 'cuda'
        assert settings['model_size'] == 'medium'
        assert settings['translation_model'] == 'nllb-1.3B'
        assert settings['tts_voice'] == 'pt_BR-faber-medium'