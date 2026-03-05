# backend/tts.py
import threading
import tempfile
import os
import subprocess
import wave
import struct
from pathlib import Path
from piper import PiperVoice

# Alias para compatibilidade - exporta TTSEngine como PiperTTSEngine
TTSEngine = None  # Será definido abaixo como alias da classe principal

class PiperTTSEngine:
    def __init__(self, device="cpu", model_name="pt_BR-faber-medium", model_path=None):
        self.device = "cpu"  # Força CPU para compatibilidade com ROCm
        self.model_name = model_name
        self.model_path = model_path
        self.voice = None

        if self.model_path is None:
            # Caminho padrão para o modelo (ajuste se necessário)
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
            # Obtém o gerador de chunks
            audio_chunks = list(self.voice.synthesize(text))
            
            # Concatena todos os chunks em um único objeto bytes
            audio_bytes = b''.join(chunk.audio_int16_bytes for chunk in audio_chunks)
            
            # Obtém parâmetros do áudio do primeiro chunk
            sample_rate = audio_chunks[0].sample_rate if audio_chunks else 22050
            sample_width = audio_chunks[0].sample_width if audio_chunks else 2
            channels = audio_chunks[0].sample_channels if audio_chunks else 1
            
            # Cria um arquivo WAV válido
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            
            with wave.open(temp.name, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)
            
            return temp.name
        except Exception as e:
            print(f"❌ Erro na síntese Piper: {e}")
            return None

    def play_audio(self, file_path):
        def play():
            try:
                subprocess.run(['ffplay', '-nodisp', '-autoexit', file_path],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Erro na reprodução: {e}")
            finally:
                try:
                    os.unlink(file_path)
                except:
                    pass
        threading.Thread(target=play, daemon=True).start()

    # Método speak para compatibilidade com a interface esperada
    def speak(self, text):
        """Método de compatibilidade - sintetiza e reproduz o texto."""
        file_path = self.synthesize(text)
        if file_path:
            self.play_audio(file_path)
            return True
        return False

    # Método stop para compatibilidade (pode ser implementado se necessário)
    def stop(self):
        """Interrompe a reprodução atual (placeholder - implementar se necessário)."""
        # Como a reprodução é feita em thread separada com ffplay,
        # seria necessário gerenciar o processo para parar.
        # Por enquanto, é um placeholder.
        pass


# Definir TTSEngine como alias para PiperTTSEngine para compatibilidade
TTSEngine = PiperTTSEngine