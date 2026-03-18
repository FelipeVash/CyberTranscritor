# utils/logger.py
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Diretório de logs padrão
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Arquivo de log padrão
DEFAULT_LOG_FILE = LOG_DIR / "transcritor.log"

# Formato dos logs
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name="transcritor", level=logging.DEBUG, log_to_file=True, log_to_console=True, file_path=None):
    """
    Configura e retorna um logger com o nome especificado.
    Por padrão, loga para arquivo (com rotação) e para o console.

    Args:
        name: Nome do logger.
        level: Nível de log (ex: logging.DEBUG).
        log_to_file: Se True, envia logs para arquivo.
        log_to_console: Se True, envia logs para console.
        file_path: Caminho opcional para o arquivo de log. Se None, usa o padrão.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Handler para arquivo
    if log_to_file:
        log_file = Path(file_path) if file_path else DEFAULT_LOG_FILE
        log_file.parent.mkdir(exist_ok=True, parents=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5_242_880, backupCount=3, encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Handler para console
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Logger global padrão
logger = setup_logger()