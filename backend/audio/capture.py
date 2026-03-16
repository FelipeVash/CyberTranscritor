"""
Audio capture module for recording from PulseAudio sinks.
Uses pulsectl to list and capture from monitor sources.
"""

import wave
import threading
import time
from pathlib import Path
import pulsectl
import numpy as np
from utils.logger import logger

class AudioCapture:
    """
    Captures audio from a PulseAudio sink monitor and saves to a WAV file.
    Also provides audio chunks in real-time for streaming processing.
    """

    def __init__(self):
        self.pulse = pulsectl.Pulse('meeting-capture')
        self.stream = None
        self.recording = False
        self.thread = None
        self.output_file = None
        self.wav_file = None
        self.on_audio_chunk = None  # callback for real-time chunks

    def list_sinks(self):
        """Return a list of sink names (including monitor sources)."""
        sinks = []
        for sink in self.pulse.sink_list():
            # Each sink has a monitor source named like "sink_name.monitor"
            monitor_name = f"{sink.name}.monitor"
            sinks.append(monitor_name)
        return sinks

    def start(self, sink_monitor_name, output_path, chunk_callback=None):
        """
        Start recording from the specified sink monitor.
        - sink_monitor_name: e.g., "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor"
        - output_path: path to save the WAV file.
        - chunk_callback: optional function to call with each audio chunk (numpy array).
        """
        if self.recording:
            logger.warning("Already recording")
            return

        self.output_file = Path(output_path)
        self.wav_file = wave.open(str(self.output_file), 'wb')
        self.wav_file.setnchannels(2)  # assume stereo, adjust if needed
        self.wav_file.setsampwidth(2)   # 16-bit
        self.wav_file.setframerate(44100)  # typical sample rate

        self.on_audio_chunk = chunk_callback
        self.recording = True
        self.thread = threading.Thread(target=self._record_thread, args=(sink_monitor_name,))
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Recording started from {sink_monitor_name} to {output_path}")

    def stop(self):
        """Stop recording and close the WAV file."""
        self.recording = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.wav_file:
            self.wav_file.close()
            self.wav_file = None
        logger.info("Recording stopped")

    def _record_thread(self, sink_monitor_name):
        """Internal thread: capture from PulseAudio monitor."""
        try:
            # Find the source by name
            sources = [s for s in self.pulse.source_list() if s.name == sink_monitor_name]
            if not sources:
                logger.error(f"Source {sink_monitor_name} not found")
                return
            source = sources[0]

            # Record in chunks
            with self.pulse.source_read(source.index) as stream:
                while self.recording:
                    data, overflow = stream.read(1024)  # read 1024 frames
                    if data:
                        # Convert to numpy array (int16)
                        audio_chunk = np.frombuffer(data, dtype=np.int16)
                        # Write to WAV file
                        self.wav_file.writeframes(data)
                        # Callback for real-time processing
                        if self.on_audio_chunk:
                            self.on_audio_chunk(audio_chunk)
                    else:
                        time.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in audio capture thread: {e}")
        finally:
            self.recording = False