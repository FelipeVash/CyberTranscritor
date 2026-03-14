# tests/test_i18n.py
import pytest
from utils.i18n import I18n, _, get_language_display
from pathlib import Path

@pytest.fixture
def i18n_instance(tmp_path):
    """Create an I18n instance with temporary locale directory."""
    locales = tmp_path / "locales"
    locales.mkdir()
    
    # Portuguese (Brazil) file - usando estrutura aninhada
    pt_file = locales / "pt-br.json"
    pt_file.write_text('''
    {
        "test": "Olá",
        "greeting": "Bom dia",
        "common": {
            "languages": {
                "pt-br": "Português",
                "en": "Inglês",
                "es": "Espanhol"
            }
        }
    }
    ''')
    
    # English file - estrutura aninhada
    en_file = locales / "en.json"
    en_file.write_text('''
    {
        "test": "Hello",
        "greeting": "Good morning",
        "common": {
            "languages": {
                "pt-br": "Portuguese",
                "en": "English",
                "es": "Spanish"
            }
        }
    }
    ''')
    
    return I18n(localedir=locales)

def test_load_language(i18n_instance):
    """Test loading different languages."""
    i18n_instance.load_language("pt-br")
    assert i18n_instance.get("test") == "Olá"
    
    i18n_instance.load_language("en")
    assert i18n_instance.get("test") == "Hello"

def test_get_with_formatting(i18n_instance):
    """Test getting translations with and without formatting."""
    i18n_instance.load_language("pt-br")
    assert i18n_instance.get("greeting") == "Bom dia"
    
    # If key doesn't exist, return the key itself
    assert i18n_instance.get("nonexistent") == "nonexistent"

def test_get_language_display(i18n_instance):
    """Test the get_language_display function."""
    i18n_instance.load_language("pt-br")
    # Should return "Português (pt-br)" from Portuguese file
    assert i18n_instance.get_language_display("pt-br") == "Português (pt-br)"
    assert i18n_instance.get_language_display("en") == "Inglês (en)"
    
    i18n_instance.load_language("en")
    # Should return "Portuguese (pt-br)" from English file
    assert i18n_instance.get_language_display("pt-br") == "Portuguese (pt-br)"
    assert i18n_instance.get_language_display("en") == "English (en)"
    
    # Test fallback when key doesn't exist
    assert i18n_instance.get_language_display("fr") == "fr (fr)"

def test_global_function(i18n_instance):
    """Test the global _() function."""
    # Replace global instance temporarily
    import utils.i18n
    utils.i18n._i18n = i18n_instance
    
    i18n_instance.load_language("pt-br")
    assert _("test") == "Olá"
    assert _("greeting") == "Bom dia"
    assert _("unknown") == "unknown"
    
    # Test global get_language_display
    utils.i18n._i18n = i18n_instance
    i18n_instance.load_language("pt-br")
    assert get_language_display("pt-br") == "Português (pt-br)"