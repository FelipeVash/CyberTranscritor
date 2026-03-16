"""
Meeting controller for handling recording, diarization, and minutes generation.
Independent controller for the meeting recording window.
"""

from pathlib import Path
import tempfile
from backend.audio.capture import AudioCapture
from utils.logger import logger

class MeetingController:
    """
    Controller for meeting recording and processing.
    """

    def __init__(self):
        self.capture = AudioCapture()
        self.audio_file = None
        self.is_recording = False
        self.on_status_update = None  # callback for UI status updates
        self.on_speaker_update = None # callback for real-time speaker (future)

    def get_sinks(self):
        """Return list of available sink monitor names."""
        return self.capture.list_sinks()

    def start_recording(self, sink_name):
        """Start recording from selected sink."""
        if self.is_recording:
            return
        # Create temporary file
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        self.audio_file = Path(temp.name)
        temp.close()

        self.capture.start(sink_name, str(self.audio_file),
                           chunk_callback=self._on_audio_chunk)
        self.is_recording = True
        self._update_status("Gravando...")

    def stop_recording(self):
        """Stop recording and trigger processing."""
        if not self.is_recording:
            return
        self.capture.stop()
        self.is_recording = False
        self._update_status("Gravação finalizada. Iniciando processamento...")
        # Here we will later call the processing pipeline in a background thread
        # For now, just indicate done
        self._update_status("Processamento concluído (placeholder)")

    def _on_audio_chunk(self, chunk):
        """Callback for real-time audio chunks (future use)."""
        # Will be used for real-time diarization with diart
        pass

    def _update_status(self, message):
        if self.on_status_update:
            self.on_status_update(message)
        logger.info(f"Status: {message}")

    def cleanup(self):
        """Clean up temporary files."""
        if self.audio_file and self.audio_file.exists():
            self.audio_file.unlink()
            logger.debug(f"Deleted temporary audio file {self.audio_file}")