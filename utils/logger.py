# utils/logger.py
"""
Logging configuration module for the Transcritor Cyberpunk project.
Provides a centralized logging setup with file rotation and console output.
All log messages should be in English to facilitate international collaboration.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Directory where log files will be stored
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Main log file path
LOG_FILE = LOG_DIR / "transcritor.log"

# Log format: timestamp - level - logger name - message
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name="transcritor", level=logging.DEBUG, log_to_file=True, log_to_console=True):
    """
    Configure and return a logger with the specified name.
    
    Args:
        name: Logger name (usually the module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: If True, log to a rotating file
        log_to_console: If True, log to console (stderr)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs from parent loggers

    # Remove any existing handlers to avoid duplication when reloading modules
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # File handler with rotation (max 5 MB, keep 3 backups)
    if log_to_file:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5_242_880, backupCount=3, encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Default global logger instance
logger = setup_logger()