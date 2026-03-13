import pytest
from unittest.mock import Mock, patch
from backend.services.translation_service import TranslationService, TranslationCache

def test_cache_hit():
    """Repetir a mesma tradução deve retornar do cache sem chamar o tradutor."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=10)
    
    text = "hello"
    source, target = "en", "pt"
    translation = "olá"
    
    # Primeira chamada
    mock_translator.translate.return_value = translation
    result1 = service.translate(text, source, target)
    assert result1 == translation
    assert mock_translator.translate.call_count == 1
    
    # Segunda chamada (deve vir do cache)
    mock_translator.translate.reset_mock()
    result2 = service.translate(text, source, target)
    assert result2 == translation
    mock_translator.translate.assert_not_called()

def test_cache_miss():
    """Textos diferentes devem gerar chamadas diferentes ao tradutor."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=10)
    
    mock_translator.translate.side_effect = ["olá", "adeus"]
    
    result1 = service.translate("hello", "en", "pt")
    result2 = service.translate("goodbye", "en", "pt")
    
    assert mock_translator.translate.call_count == 2
    assert result1 == "olá"
    assert result2 == "adeus"

def test_cache_clear():
    """Limpar o cache deve remover todas as entradas."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=10)
    
    mock_translator.translate.return_value = "olá"
    service.translate("hello", "en", "pt")
    assert service.cache.stats()["size"] == 1
    
    service.clear_cache()
    assert service.cache.stats()["size"] == 0
    assert service.cache.stats()["hits"] == 0
    assert service.cache.stats()["misses"] == 0

def test_cache_lru():
    """Quando o cache atinge o limite, a entrada mais antiga deve ser removida."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=2)
    
    mock_translator.translate.side_effect = ["um", "dois", "três"]
    
    service.translate("text1", "en", "pt")
    service.translate("text2", "en", "pt")
    assert service.cache.stats()["size"] == 2
    
    # Esta chamada deve remover "text1" (o mais antigo)
    service.translate("text3", "en", "pt")
    assert service.cache.stats()["size"] == 2
    
    # "text1" não deve estar mais no cache
    cached = service.cache.get("text1", "en", "pt")
    assert cached is None

def test_cache_stats():
    """As estatísticas do cache devem refletir acertos e erros."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=10)
    
    mock_translator.translate.return_value = "olá"
    
    service.translate("hello", "en", "pt")  # miss
    service.translate("hello", "en", "pt")  # hit
    service.translate("goodbye", "en", "pt") # miss
    
    stats = service.cache_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 2
    assert stats["size"] == 2