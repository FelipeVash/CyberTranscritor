# tests/test_logger.py
import logging
from utils.logger import setup_logger

def test_logger_initialization():
    """Testa se o logger é inicializado sem erros."""
    logger = setup_logger("test_init", log_to_console=False, log_to_file=False)
    assert logger.name == "test_init"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 0

def test_logger_writes_to_file(tmp_path):
    """Testa se o logger escreve em um arquivo temporário."""
    log_file = tmp_path / "test.log"
    test_logger = setup_logger(
        "test_file",
        log_to_file=True,
        log_to_console=False,
        file_path=log_file
    )
    test_logger.info("Test message")
    # Força o flush dos handlers
    for handler in test_logger.handlers:
        handler.flush()
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content