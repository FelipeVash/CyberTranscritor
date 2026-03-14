# tests/test_translation_cache.py
import pytest
from unittest.mock import Mock
from backend.services.translation_service import TranslationService, TranslationCache

def test_cache_hit():
    """Repeating the same translation should return from cache without calling translator."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=10)
    
    text = "hello"
    source, target = "en", "pt"
    model_size = "nllb-200M"
    translation = "olá"
    
    # First call
    mock_translator.translate.return_value = translation
    result1 = service.translate_with_translator(mock_translator, text)
    assert result1 == translation
    assert mock_translator.translate.call_count == 1
    
    # Second call (should come from cache)
    mock_translator.translate.reset_mock()
    result2 = service.translate_with_translator(mock_translator, text)
    assert result2 == translation
    mock_translator.translate.assert_not_called()

def test_cache_miss():
    """Different texts should cause different calls to translator."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=10)
    
    mock_translator.translate.side_effect = ["olá", "adeus"]
    
    result1 = service.translate_with_translator(mock_translator, "hello")
    result2 = service.translate_with_translator(mock_translator, "goodbye")
    
    assert mock_translator.translate.call_count == 2
    assert result1 == "olá"
    assert result2 == "adeus"

def test_cache_clear():
    """Clearing the cache should remove all entries."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=10)
    
    mock_translator.translate.return_value = "olá"
    service.translate_with_translator(mock_translator, "hello")
    assert service.cache.stats()["size"] == 1
    
    service.clear_cache()
    assert service.cache.stats()["size"] == 0
    assert service.cache.stats()["hits"] == 0
    assert service.cache.stats()["misses"] == 0

def test_cache_lru():
    """When cache reaches limit, oldest entry should be removed."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=2)
    
    mock_translator.translate.side_effect = ["um", "dois", "três"]
    
    # Set model_size manually on translator mock
    mock_translator.source_lang = "en"
    mock_translator.target_lang = "pt"
    mock_translator.model_size = "nllb-200M"
    
    service.translate_with_translator(mock_translator, "text1")
    service.translate_with_translator(mock_translator, "text2")
    assert service.cache.stats()["size"] == 2
    
    # This call should remove "text1" (the oldest)
    service.translate_with_translator(mock_translator, "text3")
    assert service.cache.stats()["size"] == 2
    
    # "text1" should no longer be in cache
    cached = service.cache.get("text1", "en", "pt", "nllb-200M")
    assert cached is None

def test_cache_stats():
    """Cache statistics should reflect hits and misses."""
    mock_model_manager = Mock()
    mock_translator = Mock()
    mock_model_manager.get_translator.return_value = mock_translator
    service = TranslationService(mock_model_manager, cache_size=10)
    
    mock_translator.source_lang = "en"
    mock_translator.target_lang = "pt"
    mock_translator.model_size = "nllb-200M"
    mock_translator.translate.return_value = "olá"
    
    service.translate_with_translator(mock_translator, "hello")  # miss
    service.translate_with_translator(mock_translator, "hello")  # hit
    service.translate_with_translator(mock_translator, "goodbye")  # miss
    
    stats = service.cache_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 2
    assert stats["size"] == 2