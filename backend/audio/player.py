# backend/audio/player.py
import subprocess
import os
import signal
import threading

class AudioPlayer:
    """Gerencia reprodução de áudio com ffplay."""
    def __init__(self):
        self.current_process = None
        self.lock = threading.RLock()

    def play(self, file_path):
        """Reproduz um arquivo de áudio, parando qualquer reprodução anterior."""
        with self.lock:
            self.stop()
            try:
                self.current_process = subprocess.Popen(
                    ['ffplay', '-nodisp', '-autoexit', file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                print(f"▶ Reprodução iniciada: PID {self.current_process.pid}")
            except Exception as e:
                print(f"Erro ao iniciar ffplay: {e}")
                self.current_process = None

    def stop(self):
        """Para a reprodução atual."""
        with self.lock:
            if self.current_process and self.current_process.poll() is None:
                print(f"🔇 Parando processo PID {self.current_process.pid}")
                try:
                    os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                self.current_process = None