#!/usr/bin/env python3
"""
Standalone meeting recorder application.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from apps.meeting.window import MeetingWindow
from core.utils.logger import logger

def main():
    logger.info("Starting Meeting Recorder")
    app = MeetingWindow()
    app.run()

if __name__ == "__main__":
    main()