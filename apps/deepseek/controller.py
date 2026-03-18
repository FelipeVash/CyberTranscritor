# apps/deepseek/controller.py
import threading
import asyncio
import torch
from core.backend.transcriber import TranscriberGPU
from core.backend.deepseek_client import DeepSeekClient
from core.backend.web_search import WebSearch
from core.backend.corrector import correct_text
from core.backend.tts import PiperTTSEngine
from core.utils.logger import logger
from core import config

class DeepSeekController:
    def __init__(self):
        self.transcriber = None
        self.deepseek_client = None
        self.web_search = None
        self.tts_engine = None
        self.last_response = None
        self._load_config()

    def _load_config(self):
        # Carrega configurações do core.config
        self.model_size = getattr(config, 'MODEL_SIZE', 'base')
        self.device = getattr(config, 'DEVICE', 'cpu')
        self.tts_voice = getattr(config, 'TTS_VOICE', 'pt_BR-faber-medium') # supondo que exista em config
        # ... outras configs se necessário

    def _ensure_transcriber(self):
        if self.transcriber is None:
            self.transcriber = TranscriberGPU(
                model_size=self.model_size,
                device=self.device
            )
        return self.transcriber

    def _ensure_deepseek(self):
        if self.deepseek_client is None:
            self.deepseek_client = DeepSeekClient()
        return self.deepseek_client

    def _ensure_web_search(self):
        if self.web_search is None:
            try:
                self.web_search = WebSearch()
            except Exception as e:
                logger.error(f"Failed to initialize WebSearch: {e}")
        return self.web_search

    def _ensure_tts(self, audio_player):
        if self.tts_engine is None and audio_player:
            try:
                self.tts_engine = PiperTTSEngine(
                    voice=self.tts_voice,
                    device="cpu",
                    audio_player=audio_player
                )
            except Exception as e:
                logger.error(f"Failed to initialize TTS: {e}")
        return self.tts_engine

    def transcribe_audio(self, audio, language="pt", apply_correction=True):
        """Transcreve áudio e retorna texto."""
        try:
            transcriber = self._ensure_transcriber()
            text = transcriber.transcribe(audio, language=language)
            if apply_correction:
                text = correct_text(text, language)
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return f"[Erro: {e}]"

    def ask_deepseek(self, prompt, enable_web_search=False, enable_thinking=False):
        """Envia prompt ao DeepSeek e retorna resposta."""
        try:
            client = self._ensure_deepseek()
            web_results = None
            if enable_web_search:
                web = self._ensure_web_search()
                if web:
                    try:
                        # WebSearch.search é assíncrono, precisamos rodar em loop
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        web_results = loop.run_until_complete(web.search(prompt, max_results=3))
                        loop.close()
                    except Exception as e:
                        logger.error(f"Web search error: {e}")

            # Construir prompt com contexto
            from core.utils.i18n import _
            if web_results:
                results_text = ""
                for i, res in enumerate(web_results, 1):
                    results_text += f"\n{i}. {res.get('title', '')}\n   {res.get('snippet', '')}\n   Source: {res.get('url', '')}\n"
                enhanced_prompt = _("prompts.deepseek_user_with_web", text=prompt, web_results=results_text)
            else:
                enhanced_prompt = _("prompts.deepseek_user", text=prompt)

            if enable_thinking:
                enhanced_prompt = _("prompts.thinking_prefix") + "\n\n" + enhanced_prompt

            response = client.ask(
                enhanced_prompt,
                system_prompt=_("prompts.deepseek_system"),
                opt_out=True,
                enable_thinking=False
            )
            self.last_response = response
            return response
        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            return f"[Erro: {e}]"

    def speak(self, text, audio_player):
        """Sintetiza e reproduz texto usando TTS."""
        tts = self._ensure_tts(audio_player)
        if not tts:
            return False
        file_path = tts.synthesize(text)
        if file_path:
            tts.play_audio(file_path)
            return True
        return False

    def stop_tts(self):
        """Para a reprodução de áudio."""
        if self.tts_engine:
            self.tts_engine.stop()