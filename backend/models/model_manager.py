# backend/models/model_manager.py
import torch
import threading
import time
from backend.transcriber import TranscriberGPU
from backend.translator import Translator

class ModelManager:
    """
    Gerencia o ciclo de vida dos modelos (transcrição e tradução).
    Mantém apenas uma instância de cada modelo por vez.
    Inclui descarregamento automático após período de inatividade.
    """
    def __init__(self, device="cuda", idle_timeout=60):  # 5 minutos padrão
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.idle_timeout = idle_timeout  # segundos

        # Modelos atuais
        self.current_transcriber = None
        self.current_transcriber_model = None
        self.current_translator = None
        self.current_translator_pair = (None, None)

        # Timer para descarregamento
        self.unload_timer = None
        self.lock = threading.RLock()

        # Último acesso (timestamp)
        self.last_access = time.time()

    def _reset_timer(self):
        """Reinicia o timer de descarregamento."""
        with self.lock:
            if self.unload_timer:
                self.unload_timer.cancel()
            self.unload_timer = threading.Timer(self.idle_timeout, self._unload_if_idle)
            self.unload_timer.daemon = True
            self.unload_timer.start()

    def _unload_if_idle(self):
        """Verifica se passou tempo suficiente desde o último acesso e descarrega."""
        with self.lock:
            if time.time() - self.last_access >= self.idle_timeout:
                print("⏰ Tempo limite de inatividade atingido. Descarregando modelos...")
                self.unload_all()
                self.unload_timer = None
            else:
                # Se ainda não passou, reinicia o timer para o tempo restante
                remaining = self.idle_timeout - (time.time() - self.last_access)
                if remaining > 0:
                    self.unload_timer = threading.Timer(remaining, self._unload_if_idle)
                    self.unload_timer.daemon = True
                    self.unload_timer.start()

    def _update_access(self):
        """Atualiza timestamp de último acesso e reinicia timer."""
        with self.lock:
            self.last_access = time.time()
            self._reset_timer()

    def get_transcriber(self, model_size="tiny"):
        """
        Retorna o transcriber, carregando-o se necessário ou se o tamanho mudou.
        """
        with self.lock:
            self._update_access()
            if (self.current_transcriber is None) or (self.current_transcriber_model != model_size):
                self.unload_transcriber()
                print(f"📥 Carregando transcriber modelo {model_size}...")
                self.current_transcriber = TranscriberGPU(model_size=model_size, device=self.device)
                self.current_transcriber_model = model_size
            return self.current_transcriber

    def get_translator(self, source_lang="pt", target_lang="en"):
        """
        Retorna o tradutor, carregando-o se necessário ou se o par de idiomas mudou.
        """
        with self.lock:
            self._update_access()
            if (self.current_translator is None) or (self.current_translator_pair != (source_lang, target_lang)):
                self.unload_translator()
                print(f"📥 Carregando tradutor {source_lang} -> {target_lang}...")
                try:
                    self.current_translator = Translator(
                        source_lang=source_lang,
                        target_lang=target_lang,
                        device=self.device
                    )
                except Exception as e:
                    print(f"❌ Falha ao carregar tradutor: {e}")
                    # Tenta novamente com uma pequena pausa (pode ser problema de cache)
                    time.sleep(2)
                    print("🔄 Tentando novamente...")
                    self.current_translator = Translator(
                        source_lang=source_lang,
                        target_lang=target_lang,
                        device=self.device
                    )
                self.current_translator_pair = (source_lang, target_lang)
            return self.current_translator

    def unload_transcriber(self):
        """Descarrega o transcriber da GPU."""
        with self.lock:
            if self.current_transcriber:
                print("📤 Descarregando transcriber...")
                del self.current_transcriber
                self.current_transcriber = None
                self.current_transcriber_model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    def unload_translator(self):
        """Descarrega o tradutor da GPU."""
        with self.lock:
            if self.current_translator:
                print("📤 Descarregando tradutor...")
                self.current_translator.unload()  # Chama o método unload do Translator
                del self.current_translator
                self.current_translator = None
                self.current_translator_pair = (None, None)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    def unload_all(self):
        """Descarrega todos os modelos."""
        with self.lock:
            self.unload_transcriber()
            self.unload_translator()
            if self.unload_timer:
                self.unload_timer.cancel()
                self.unload_timer = None
            print("🧹 Todos os modelos descarregados.")

    def __del__(self):
        self.unload_all()