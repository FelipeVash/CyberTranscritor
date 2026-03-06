# backend/audio/recorder.py
"""
Audio recording module using sounddevice.
Records audio in real-time, stores chunks in a buffer, and returns a numpy array.
All logging is done through the centralized logger.
"""

import sounddevice as sd
import numpy as np
import threading
from utils.logger import logger

class AudioRecorder:
    """
    Simple audio recorder that captures microphone input.
    Records in a background thread and can optionally call a callback per chunk.
    """

    def __init__(self, samplerate=16000, channels=1, blocksize=1600, callback=None):
        """
        Initialize the recorder.

        Args:
            samplerate: Sampling rate in Hz (default 16000)
            channels: Number of channels (1 for mono)
            blocksize: Number of frames per buffer
            callback: Optional function called with each audio chunk
        """
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize
        self.callback = callback
        self.is_recording = False
        self.audio_buffer = []
        self.thread = None
        logger.debug(f"AudioRecorder initialized (rate={samplerate}, channels={channels})")

    def start(self):
        """Start recording audio."""
        self.audio_buffer = []
        self.is_recording = True
        self.thread = threading.Thread(target=self._record, daemon=True)
        self.thread.start()
        logger.info("Recording started")

    def stop(self):
        """
        Stop recording and return the captured audio as a numpy array.

        Returns:
            numpy array of audio samples (float32, mono)
        """
        self.is_recording = False
        if self.thread:
            self.thread.join(timeout=2)
        if not self.audio_buffer:
            logger.warning("No audio recorded")
            return np.array([])
        audio = np.concatenate(self.audio_buffer)
        logger.info(f"Recording stopped, captured {len(audio)} samples")
        return audio

    def _record(self):
        """Internal method that runs the recording loop in a thread."""
        with sd.InputStream(samplerate=self.samplerate, channels=self.channels,
                            blocksize=self.blocksize, dtype='float32') as stream:
            while self.is_recording:
                audio_chunk, overflowed = stream.read(self.blocksize)
                if overflowed:
                    logger.warning("Overflow detected!")
                if audio_chunk.shape[1] > 1:
                    # Convert stereo to mono by averaging
                    audio_chunk = np.mean(audio_chunk, axis=1)
                else:
                    audio_chunk = audio_chunk.flatten()
                self.audio_buffer.append(audio_chunk.copy())
                if self.callback:
                    self.callback(audio_chunk)