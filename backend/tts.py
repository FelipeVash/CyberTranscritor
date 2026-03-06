# backend/tts.py
import threading
import tempfile
import os
import wave
from pathlib import Path
from piper import PiperVoice

# Alias para compatibilidade
TTSEngine = None

class PiperTTSEngine:
    def __init__(self, device="cpu", model_name="pt_BR-faber-medium", model_path=None, audio_player=None):
        self.device = "cpu"
        self.model_name = model_name
        self.model_path = model_path
        self.audio_player = audio_player  # Recebe o player externo
        self.voice = None
        self.current_temp_file = None
        self.lock = threading.RLock()

        if self.model_path is None:
            self.model_path = Path.home() / ".local/share/piper" / "pt_BR" / "faber" / "medium" / "faber-medium.onnx"

    def load_model(self):
        if self.voice is not None:
            return True
        try:
            print(f"Carregando Piper TTS de: {self.model_path}")
            if not self.model_path.exists():
                print(f"❌ Arquivo não encontrado: {self.model_path}")
                return False
            self.voice = PiperVoice.load(self.model_path, use_cuda=False)
            print("✅ Piper TTS carregado com sucesso (em CPU)!")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar Piper TTS: {e}")
            return False

    def synthesize(self, text):
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

            return temp_path
        except Exception as e:
            print(f"❌ Erro na síntese Piper: {e}")
            return None

    def play_audio(self, file_path):
        """Reproduz o arquivo usando o AudioPlayer externo."""
        if self.audio_player:
            self.audio_player.play(file_path)
        else:
            print("⚠️ Nenhum AudioPlayer disponível para reprodução.")

    def speak(self, text):
        """Sintetiza e reproduz o texto."""
        file_path = self.synthesize(text)
        if file_path:
            self.play_audio(file_path)
            return True
        return False

    def stop(self):
        """Interrompe a reprodução via AudioPlayer."""
        if self.audio_player:
            self.audio_player.stop()

    def unload_model(self):
        if self.voice:
            del self.voice
            self.voice = None
        print("Modelo TTS descarregado.")

    def __del__(self):
        self.unload_model()

# Definir TTSEngine como alias
TTSEngine = PiperTTSEngine