# backend/background/background_recorder.py
import threading
from backend.audio.recorder import AudioRecorder
import config

class BackgroundRecorder:
    def __init__(self, controller):
        self.controller = controller
        self.recording = False
        self.recorder = None
        self.timer = None

    def start(self):
        if self.recording:
            return
        self.recording = True
        self.recorder = AudioRecorder(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            callback=self.on_audio_chunk
        )
        self.recorder.start()
        self.controller.show_notification("🎤 Gravação iniciada", "Fale agora. Pressione Super+0 novamente para parar.")
        self.reset_timer()

    def stop(self, from_timer=False):
        if not self.recording:
            return
        self.recording = False
        if self.timer:
            self.timer.cancel()
            self.timer = None
        audio = self.recorder.stop()
        if audio.size == 0:
            if from_timer:
                self.controller.show_notification("Nada gravado", "Tempo limite de silêncio atingido.")
            else:
                self.controller.show_notification("Nada gravado", "Nenhum áudio detectado.")
            return
        self.controller.show_notification("⏳ Processando", "Transcrevendo e consultando DeepSeek...")
        self.process_audio(audio)

    def on_audio_chunk(self, chunk):
        self.reset_timer()

    def reset_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(5.0, lambda: self.stop(from_timer=True))
        self.timer.start()

    def process_audio(self, audio):
        # Aqui você pode implementar a lógica de processamento em background
        # Por enquanto, apenas notifica
        self.controller.show_notification("Background", "Áudio capturado, mas processamento não implementado.")