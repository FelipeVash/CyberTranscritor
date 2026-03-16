#!/usr/bin/env python3
"""
Independent meeting recording application.
Run this directly to open the meeting window.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from controller.meeting_controller import MeetingController
from frontend.meeting_window import MeetingWindow
from utils.logger import logger

def main():
    logger.info("Starting Meeting Recorder")
    controller = MeetingController()
    app = MeetingWindow(controller)
    app.run()

if __name__ == "__main__":
    main()