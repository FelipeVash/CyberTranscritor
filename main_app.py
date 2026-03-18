# main.py
"""
Entry point for the Cyberpunk Transcription Studio application.
Initializes the controller and starts the GUI main loop.
"""

from core.controller.app_controller import AppController
from core.frontend.main_window import TranscriptionStudio as MainWindow
from core.utils.logger import logger

def main():
    """Initialize and run the application."""
    logger.info("Starting Cyberpunk Transcription Studio")
    controller = AppController()
    app = MainWindow(controller)
    app.root.mainloop()
    logger.info("Application terminated")

if __name__ == "__main__":
    main()