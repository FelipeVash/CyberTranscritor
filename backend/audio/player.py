# backend/audio/player.py
"""
Audio playback module using ffplay.
Manages a single playback process and allows stopping.
All logging is done through the centralized logger.
"""

import subprocess
import os
import signal
import threading
from utils.logger import logger

class AudioPlayer:
    """
    Simple audio player that uses ffplay to play WAV files.
    Only one playback can be active at a time.
    """

    def __init__(self):
        """Initialize the player with no active process."""
        self.current_process = None
        self.lock = threading.RLock()
        logger.debug("AudioPlayer initialized")

    def play(self, file_path):
        """
        Play a WAV file, stopping any currently playing audio.

        Args:
            file_path: Path to the WAV file
        """
        with self.lock:
            self.stop()
            try:
                self.current_process = subprocess.Popen(
                    ['ffplay', '-nodisp', '-autoexit', file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid  # Create a new process group
                )
                logger.info(f"Started playback: PID {self.current_process.pid}")
            except Exception as e:
                logger.error(f"Failed to start ffplay: {e}")
                self.current_process = None

    def stop(self):
        """Stop the current playback if any."""
        with self.lock:
            if self.current_process and self.current_process.poll() is None:
                pid = self.current_process.pid
                logger.debug(f"Stopping playback process PID {pid}")
                try:
                    # Kill the entire process group
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                self.current_process = None
                logger.info("Playback stopped")