#!/usr/bin/env python3
"""
Entry point for standalone DeepSeek Chat application.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from apps.deepseek.window import DeepSeekWindow
from core.utils.logger import logger

def main():
    logger.info("Starting DeepSeek Chat")
    app = DeepSeekWindow()
    app.window.mainloop()

if __name__ == "__main__":
    main()