# backend/tts.py
"""
Text-to-Speech module using Piper TTS.
Handles synthesis of text to speech and playback via AudioPlayer.
All logging is done through the centralized logger.
"""

import threading
import tempfile
import os
import wave
from pathlib import Path
from piper import PiperVoice
from utils.logger import logger

# Alias for compatibility (will be set after class definition)
TTSEngine = None

class PiperTTSEngine:
    """
    Piper-based TTS engine.
    Synthesizes speech and plays it using an external AudioPlayer.
    """

    def __init__(self, device="cpu", model_name="pt_BR-faber-medium", model_path=None, audio_player=None):
        """
        Initialize the TTS engine.

        Args:
            device: Device to run inference on ('cpu' only for now)
            model_name: Name of the Piper voice model
            model_path: Path to the model file (if None, uses default location)
            audio_player: AudioPlayer instance for playback
        """
        self.device = "cpu"  # Force CPU for compatibility with ROCm
        self.model_name = model_name
        self.model_path = model_path
        self.audio_player = audio_player
        self.voice = None
        self.current_temp_file = None
        self.lock = threading.RLock()

        if self.model_path is None:
            # Default model path (adjust if necessary)
            self.model_path = Path.home() / ".local/share/piper" / "pt_BR" / "faber" / "medium" / "faber-medium.onnx"

    def load_model(self):
        """Load the Piper voice model if not already loaded."""
        if self.voice is not None:
            return True
        try:
            logger.info(f"Loading Piper TTS from: {self.model_path}")
            if not self.model_path.exists():
                logger.error(f"Model file not found: {self.model_path}")
                return False
            self.voice = PiperVoice.load(self.model_path, use_cuda=False)
            logger.info("Piper TTS loaded successfully (CPU)")
            return True
        except Exception as e:
            logger.error(f"Failed to load Piper TTS: {e}")
            return False

    def synthesize(self, text):
        """
        Synthesize text to a temporary WAV file.

        Args:
            text: Text to synthesize

        Returns:
            Path to the temporary WAV file, or None on failure.
        """
        if not self.load_model():
            return None
        try:
            audio_chunks = list(self.voice.synthesize(text))
            audio_bytes = b''.join(chunk.audio_int16_bytes for chunk in audio_chunks)
            sample_rate = audio_chunks[0].sample_rate if audio_chunks else 22050
            sample_width = audio_chunks[0].sample_width if audio_chunks else 2
            channels = audio_chunks[0].sample_channels if audio_chunks else 1

            temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp.name
            temp.close()

            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)

            logger.debug(f"Synthesized audio to {temp_path}")
            return temp_path
        except Exception as e:
            logger.error(f"Piper synthesis failed: {e}")
            return None

    def play_audio(self, file_path):
        """
        Play the synthesized audio using the external AudioPlayer.

        Args:
            file_path: Path to the WAV file
        """
        with self.lock:
            self.current_temp_file = file_path
            if self.audio_player:
                logger.debug(f"Playing audio via AudioPlayer: {file_path}")
                self.audio_player.play(file_path)
            else:
                logger.warning("No AudioPlayer available for playback")

    def speak(self, text):
        """
        Synthesize and play text (convenience method).

        Args:
            text: Text to speak

        Returns:
            True if successful, False otherwise.
        """
        file_path = self.synthesize(text)
        if file_path:
            self.play_audio(file_path)
            return True
        return False

    def stop(self):
        """Stop any ongoing playback via AudioPlayer."""
        if self.audio_player:
            logger.debug("Stopping audio via AudioPlayer")
            self.audio_player.stop()
        self._cleanup_temp()

    def _cleanup_temp(self):
        """Remove the temporary audio file if it exists."""
        if self.current_temp_file and os.path.exists(self.current_temp_file):
            try:
                os.unlink(self.current_temp_file)
                logger.debug(f"Removed temporary file: {self.current_temp_file}")
            except Exception as e:
                logger.error(f"Failed to remove temporary file: {e}")
            finally:
                self.current_temp_file = None

    def unload_model(self):
        """Unload the model and clean up resources."""
        self.stop()
        if self.voice:
            del self.voice
            self.voice = None
        logger.info("TTS model unloaded")

    def __del__(self):
        self.unload_model()

# Define TTSEngine as alias for compatibility
TTSEngine = PiperTTSEngine