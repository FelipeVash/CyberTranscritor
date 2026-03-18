#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from apps.transcritor.window import TranscriptionStudio as MainWindow
from core.controller.app_controller import AppController
from core.utils.logger import logger

def main():
    logger.info("Starting Cyberpunk Transcription Studio")
    controller = AppController()
    app = MainWindow(controller)
    app.root.mainloop()

if __name__ == "__main__":
    main()
