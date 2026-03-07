# tests/test_i18n.py
import pytest
from utils.i18n import I18n, _
from pathlib import Path

@pytest.fixture
def i18n_instance(tmp_path):
    """Cria uma instância de I18n com diretório temporário."""
    locales = tmp_path / "locales"
    locales.mkdir()
    pt_file = locales / "pt-br.json"
    pt_file.write_text('{"test": "Olá", "greeting": "Bom dia"}')
    en_file = locales / "en.json"
    en_file.write_text('{"test": "Hello", "greeting": "Good morning"}')
    return I18n(localedir=locales)

def test_load_language(i18n_instance):
    i18n_instance.load_language("pt-br")
    assert i18n_instance.get("test") == "Olá"
    i18n_instance.load_language("en")
    assert i18n_instance.get("test") == "Hello"

def test_get_with_formatting(i18n_instance):
    i18n_instance.load_language("pt-br")
    assert i18n_instance.get("greeting") == "Bom dia"
    # Se a chave não existir, retorna a própria chave
    assert i18n_instance.get("nonexistent") == "nonexistent"

def test_global_function(i18n_instance):
    # Substitui a instância global temporariamente
    import utils.i18n
    utils.i18n._i18n = i18n_instance
    i18n_instance.load_language("pt-br")
    assert _("test") == "Olá"
    assert _("greeting") == "Bom dia"
    assert _("unknown") == "unknown"