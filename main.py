# main.py
"""
Entry point for the Cyberpunk Transcription Studio application.
Initializes the controller and starts the GUI main loop.
"""

from controller.app_controller import AppController
from frontend.main_window import TranscriptionStudio
from utils.logger import logger

def main():
    """Initialize and run the application."""
    logger.info("Starting Cyberpunk Transcription Studio")
    controller = AppController()
    app = TranscriptionStudio(controller)
    app.root.mainloop()
    logger.info("Application terminated")

if __name__ == "__main__":
    main()