# frontend/deepseek_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
from datetime import datetime
import sounddevice as sd
import numpy as np
import subprocess
import traceback
import asyncio
import os
import signal

from backend.audio_recorder import AudioRecorder
from backend.deepseek_client import DeepSeekClient
from backend.transcriber import TranscriberGPU
from backend.tts import PiperTTSEngine
from backend.web_search import WebSearch
from backend.corrector import correct_text
import config
from utils.tooltip import ToolTip

class DeepSeekWindow:
    def __init__(self, parent, main_app, initial_prompt=None, initial_response=None):
        print("🟢 DeepSeekWindow: iniciando __init__")
        self.parent = parent
        self.main_app = main_app

        # Determina o dispositivo (GPU se disponível)
        if main_app is not None and hasattr(main_app, 'device'):
            device = main_app.device.get()
        else:
            device = "cpu"

        # Inicializa o TTS (Piper) – falhas não impedem a abertura da janela
        self.tts_engine = None
        try:
            self.tts_engine = PiperTTSEngine(device="cpu")  # força CPU para compatibilidade
            print("✅ TTS Engine (Piper) inicializado")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar TTS: {e}")
            traceback.print_exc()

        # Processo de reprodução atual (para poder interromper)
        self.current_play_process = None

        # Inicializa mecanismo de busca
        self.web_search = None
        try:
            self.web_search = WebSearch()
            print("✅ WebSearch inicializado")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar WebSearch: {e}")

        self.window = None
        self.is_recording = False
        self.recorder = None
        self.transcriber = main_app.transcriber if main_app is not None else None
        self.deepseek_client = main_app.deepseek_client if main_app is not None else None
        self.last_response = None
        self.chat_history = []

        # Variáveis para opções de consulta
        self.enable_thinking = tk.BooleanVar(value=False)
        self.enable_web_search = tk.BooleanVar(value=False)
        self.enable_correction = tk.BooleanVar(value=True)

        try:
            self.setup_ui()
            self.setup_bindings()
            if initial_prompt:
                self.send_to_deepseek(initial_prompt, initial_response)
            print("🟢 DeepSeekWindow: inicialização concluída")
        except Exception as e:
            print(f"❌ Erro ao configurar janela DeepSeek: {e}")
            traceback.print_exc()
            messagebox.showerror("Erro", f"Não foi possível criar a janela DeepSeek:\n{e}")
            # Não relançamos a exceção para não quebrar a aplicação principal
            # raise

    def setup_ui(self):
        print("🔵 setup_ui: criando janela Toplevel")
        self.window = tb.Toplevel(self.parent)
        self.window.title("🤖 DeepSeek - Consulta por Áudio")
        self.window.geometry("900x1100")
        self.window.focus_force()
        print("🔵 setup_ui: janela criada")

        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.btn_record = ttk.Button(control_frame, text="▶ INICIAR GRAVAÇÃO",
                                      style="Pink.TButton", width=20, command=self.toggle_recording)
        self.btn_record.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_record, "Iniciar gravação de áudio (Ctrl+R)")

        self.btn_send = ttk.Button(control_frame, text="📤 ENVIAR TEXTO",
                                   style="Cyan.TButton", width=15, command=self.send_text)
        self.btn_send.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_send, "Enviar texto digitado (Enter)")

        self.btn_stop_audio = ttk.Button(control_frame, text="⏹ Parar Áudio",
                                         style="secondary", width=15, command=self.stop_audio)
        self.btn_stop_audio.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_stop_audio, "Parar a reprodução de áudio em andamento (Super+.)")

        if self.tts_engine:
            self.btn_tts = ttk.Button(control_frame, text="🔊 Ouvir resposta",
                                       style="Cyan.TButton", width=15, command=self.play_last_response)
            self.btn_tts.pack(side=tk.LEFT, padx=2)
            ToolTip(self.btn_tts, "Ouvir a última resposta (TTS)")
        else:
            self.btn_tts = ttk.Button(control_frame, text="🔊 TTS indisponível",
                                       style="secondary", width=15, state="disabled")
            self.btn_tts.pack(side=tk.LEFT, padx=2)
            ToolTip(self.btn_tts, "TTS não disponível")

        self.status_label = tk.Label(control_frame, text="⏹ Parado", fg="#888888")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Frame de opções
        options_frame = ttk.LabelFrame(self.window, text="⚙️ Opções de Consulta", padding=5)
        options_frame.pack(fill="x", padx=10, pady=5)

        chk_think = ttk.Checkbutton(options_frame, text="Deep Think (raciocínio detalhado)",
                                     variable=self.enable_thinking, bootstyle="info")
        chk_think.pack(side=tk.LEFT, padx=5)
        ToolTip(chk_think, "Ativa o modo de raciocínio profundo do modelo")

        chk_web = ttk.Checkbutton(options_frame, text="Pesquisa na Internet",
                                   variable=self.enable_web_search, bootstyle="info")
        chk_web.pack(side=tk.LEFT, padx=5)
        ToolTip(chk_web, "Permite busca atualizada (via DuckDuckGo)")

        chk_correct = ttk.Checkbutton(options_frame, text="Corrigir texto transcrito",
                                       variable=self.enable_correction, bootstyle="info")
        chk_correct.pack(side=tk.LEFT, padx=5)
        ToolTip(chk_correct, "Corrige automaticamente a transcrição antes de enviar")

        # Histórico
        hist_frame = ttk.LabelFrame(self.window, text="📜 Histórico", padding=10)
        hist_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.hist_area = scrolledtext.ScrolledText(hist_frame, wrap=tk.WORD, font=("Consolas", 10),
                                                    bg="#1e1e1e", fg="#d4d4d4", state=tk.DISABLED)
        self.hist_area.pack(fill="both", expand=True)

        # Entrada de texto
        input_frame = ttk.LabelFrame(self.window, text="✏️ Entrada (digite ou use áudio)", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        self.input_area = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, font=("Consolas", 11),
                                                     bg="#1e1e1e", fg="#d4d4d4", height=4)
        self.input_area.pack(fill="x", padx=5, pady=5)

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="📤 ENVIAR TEXTO",
                   style="Cyan.TButton", command=self.send_text).pack(side=tk.RIGHT, padx=5)

        dica = tk.Label(input_frame, text="Enter: enviar | Shift+Enter: nova linha | Ctrl+R: gravar | Esc: fechar | Super+.: parar áudio",
                        fg="#888888", bg="#2b2b2b", font=("Segoe UI", 9))
        dica.pack(pady=2)
        print("🔵 setup_ui: concluído")

    def setup_bindings(self):
        print("🟡 setup_bindings: configurando atalhos")
        self.input_area.bind("<Return>", self.on_enter_press)
        self.input_area.bind("<Shift-Return>", self.on_shift_enter)
        self.window.bind("<Escape>", lambda e: self.destroy())
        self.window.bind("<Control-r>", lambda e: self.toggle_recording())
        self.window.bind("<Control-R>", lambda e: self.toggle_recording())

        # Os binds com Super foram removidos porque causam erro no Tkinter.
        # O atalho global será tratado via D-Bus (Super + .)
        # self.window.bind("<Super-period>", lambda e: self.stop_audio())
        # self.window.bind("<Super-KP_Decimal>", lambda e: self.stop_audio())
        print("🟡 setup_bindings: concluído (sem binds Super)")

    def stop_audio(self):
        """Interrompe a reprodução de áudio em andamento."""
        if self.current_play_process and self.current_play_process.poll() is None:
            print("🔇 Interrompendo reprodução de áudio")
            self.current_play_process.terminate()
            try:
                self.current_play_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.current_play_process.kill()
            self.current_play_process = None
            self.show_notification("Áudio interrompido", "Reprodução cancelada pelo usuário.")
        else:
            print("Nenhum áudio em reprodução")

    def on_enter_press(self, event):
        self.send_text()
        return "break"

    def on_shift_enter(self, event):
        self.input_area.insert(tk.INSERT, "\n")
        return "break"

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_and_send()

    def start_recording(self):
        self.recorder = AudioRecorder(samplerate=config.SAMPLE_RATE, channels=config.CHANNELS)
        self.is_recording = True
        self.recorder.start()
        self.btn_record.config(text="⏹ PARAR E ENVIAR", style="success.TButton")
        self.status_label.config(text="🔴 Gravando...", fg="red")

    def stop_and_send(self):
        self.is_recording = False
        audio = self.recorder.stop()
        self.btn_record.config(text="▶ INICIAR GRAVAÇÃO", style="Pink.TButton")
        self.status_label.config(text="⏳ Transcrevendo...", fg="orange")

        if audio.size == 0:
            messagebox.showwarning("Aviso", "Nenhum áudio gravado.")
            self.status_label.config(text="⏹ Parado", fg="#888888")
            return

        if self.transcriber is None:
            try:
                self.transcriber = TranscriberGPU(
                    model_size=self.main_app.model_size.get() if self.main_app else "tiny",
                    device=self.main_app.device.get() if self.main_app else "cuda"
                )
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao criar transcriber: {e}")
                self.status_label.config(text="⏹ Parado", fg="#888888")
                return

        def transcribe_task():
            try:
                lang = self.main_app.current_language.get() if self.main_app else "pt"
                text = self.transcriber.transcribe(audio, language=lang)

                if text.startswith("[Erro:") or text.startswith("❌") or "áudio muito baixo" in text.lower():
                    self.window.after(0, lambda: messagebox.showerror("Erro na transcrição", text))
                    self.window.after(0, lambda: self.status_label.config(text="⏹ Parado", fg="#888888"))
                    return

                if self.enable_correction.get():
                    print("✍️ Aplicando correção gramatical...")
                    text = correct_text(text, lang)

                self.window.after(0, lambda: self.send_to_deepseek(text))
            except Exception as e:
                self.window.after(0, lambda: messagebox.showerror("Erro", f"Falha na transcrição: {e}"))
                self.window.after(0, lambda: self.status_label.config(text="⏹ Parado", fg="#888888"))

        threading.Thread(target=transcribe_task, daemon=True).start()

    def send_text(self):
        text = self.input_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "Nada para enviar.")
            return
        self.input_area.delete(1.0, tk.END)
        if self.enable_correction.get():
            lang = self.main_app.current_language.get() if self.main_app else "pt"
            text = correct_text(text, lang)
        self.send_to_deepseek(text)

    def send_to_deepseek(self, text, pre_response=None):
        if self.deepseek_client is None:
            try:
                self.deepseek_client = DeepSeekClient()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao configurar DeepSeek: {e}")
                return

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._add_to_history("user", text, timestamp)

        if pre_response:
            self.last_response = pre_response
            self._add_to_history("assistant", pre_response, timestamp)
            self.status_label.config(text="✅ Resposta pré-carregada", fg="green")
            self._auto_play_response(pre_response)
            return

        self.status_label.config(text="⏳ Consultando DeepSeek...", fg="orange")

        def task():
            try:
                web_results = None
                if self.enable_web_search.get() and self.web_search:
                    print("🌐 Buscando na internet...")
                    web_results = asyncio.run(self.web_search.search(text, max_results=3))
                    if web_results:
                        print(f"✅ Encontrados {len(web_results)} resultados")

                enhanced_prompt = text
                if web_results:
                    enhanced_prompt = self._build_prompt_with_web(text, web_results)

                resposta = self.deepseek_client.ask(
                    enhanced_prompt,
                    opt_out=True,
                    enable_thinking=self.enable_thinking.get(),
                    enable_web_search=False
                )
                self.last_response = resposta
                self.window.after(0, lambda: self._add_to_history("assistant", resposta, datetime.now().strftime("%H:%M:%S")))
                self.window.after(0, lambda: self.status_label.config(text="✅ Resposta recebida", fg="green"))
                self.window.after(0, lambda: self._auto_play_response(resposta))
            except Exception as e:
                self.window.after(0, lambda: messagebox.showerror("Erro", f"Falha na consulta: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def _build_prompt_with_web(self, original_query, web_results):
        prompt = f"""Pergunta do usuário: {original_query}

Resultados de pesquisa na internet (atuais):
"""
        for i, res in enumerate(web_results, 1):
            prompt += f"\n{i}. {res['title']}\n   {res['snippet']}\n   Fonte: {res['url']}\n"

        prompt += "\nCom base nas informações acima, responda à pergunta do usuário de forma completa e atualizada."
        return prompt

    def _auto_play_response(self, text):
        if not self.tts_engine:
            return
        # Só impede execução se houver blocos de código
        if '```' in text:
            print("🔇 Resposta contém código, não reproduzindo automaticamente.")
            return
        print("🔊 Auto-play ativado")
        self.play_response(text)

    def play_last_response(self):
        if not self.tts_engine:
            messagebox.showerror("Erro", "TTS não disponível.")
            return
        if not self.last_response:
            messagebox.showinfo("Info", "Nenhuma resposta disponível.")
            return
        print("🔊 Reproduzindo última resposta")
        self.play_response(self.last_response)

    def play_response(self, text):
        """Reproduz uma resposta usando TTS."""
        file_path = self.tts_engine.synthesize(text)
        if file_path:
            self._play_audio_file(file_path)

    def _play_audio_file(self, file_path):
        """Reproduz um arquivo de áudio e gerencia o processo."""
        def play():
            try:
                self.current_play_process = subprocess.Popen(
                    ['ffplay', '-nodisp', '-autoexit', file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.current_play_process.wait()
            except Exception as e:
                print(f"Erro na reprodução: {e}")
            finally:
                self.current_play_process = None
                try:
                    os.unlink(file_path)
                except:
                    pass
        threading.Thread(target=play, daemon=True).start()

    def show_notification(self, title, message):
        try:
            subprocess.run(['notify-send', title, message])
        except Exception as e:
            print(f"Erro na notificação: {e}")

    def _add_to_history(self, role, content, timestamp):
        self.hist_area.config(state=tk.NORMAL)
        if role == "user":
            self.hist_area.insert(tk.END, f"[{timestamp}] Você:\n", "user")
            self.hist_area.tag_configure("user", foreground="#00ffbf")
        else:
            self.hist_area.insert(tk.END, f"[{timestamp}] DeepSeek:\n", "assistant")
            self.hist_area.tag_configure("assistant", foreground="#ff00ff")
        self.hist_area.insert(tk.END, content + "\n\n")
        self.hist_area.see(tk.END)
        self.hist_area.config(state=tk.DISABLED)

    def destroy(self):
        print("🔻 Fechando janela DeepSeek")
        if self.tts_engine:
            self.tts_engine.unload_model()
        if self.window:
            self.window.destroy()