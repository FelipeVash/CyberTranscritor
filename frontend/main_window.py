# frontend/main_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import tkinter.font as tkfont
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
from pathlib import Path
import sys
import torch
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import queue
import traceback
import subprocess

# Configura o main loop do GLib para D-Bus
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

# Fila para comunicação entre a thread GLib e a thread principal do Tkinter
dbus_queue = queue.Queue()

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from backend.transcriber import TranscriberGPU
from backend.translator import Translator
from backend.deepseek_client import DeepSeekClient
from backend.corrector import correct_text
from backend.audio_recorder import AudioRecorder
from backend.tts import TTSEngine
from frontend.dialogs import show_correction_dialog
from frontend.widgets import FormatToolbar
from frontend.styles import configure_styles
from frontend.deepseek_window import DeepSeekWindow
from utils.constants import ALL_LANGUAGES, ALL_LANGUAGE_NAMES, LT_LANGUAGE_MAP
from utils.helpers import handle_enter
from utils.tooltip import ToolTip
from utils.config_persistence import load_config, save_config
from frontend.tray_icon import TrayIcon

class TranscriptionStudio(dbus.service.Object):
    def __init__(self):
        self.root = tb.Window(themename="darkly")
        self.root.title("Studio de Transcrição Cyberpunk")
        self.root.geometry("1100x1000")

        configure_styles(self.root.style)

        # Registra o objeto D-Bus
        try:
            bus = dbus.SessionBus()
            bus_name = dbus.service.BusName('studio.transcritor', bus)
            dbus.service.Object.__init__(self, bus_name, '/studio/transcritor')
            print("✅ Objeto D-Bus registrado")
        except Exception as e:
            print(f"❌ Erro ao registrar D-Bus: {e}")
            traceback.print_exc()

        # Carrega configurações salvas
        saved = load_config()
        self.model_size = tk.StringVar(value=saved.get("model_size", config.MODEL_SIZE))
        self.device = tk.StringVar(value=saved.get("device", config.DEVICE))
        self.current_language = tk.StringVar(value=saved.get("source_language", "pt"))
        self.translate_target = tk.StringVar(value=saved.get("target_language", "en"))

        self.is_recording = False
        self.recorder = None
        self.transcriber = None
        self.translator = None
        self.deepseek_window = None  # referência para a janela DeepSeek
        self.tts_engine = TTSEngine(device=self.device.get())

        self.all_languages = ALL_LANGUAGES
        self.all_language_names = ALL_LANGUAGE_NAMES
        self.lt_language_map = LT_LANGUAGE_MAP

        self.deepseek_client = None
        self.deepseek_model = tk.StringVar(value="deepseek-chat")
        self.last_number = 0

        # Trava para evitar múltiplas execuções simultâneas
        self.busy = False

        # Variáveis para gravação em background
        self.background_recording = False
        self.background_recorder = None
        self.background_timer = None
        self.background_audio_buffer = []

        self.setup_ui()
        self.check_microphone()
        self.setup_bindings()
        self.check_dbus_queue()

        # Inicia o processamento periódico dos eventos GLib (em vez de thread)
        self.process_glib_events()

        # Inicia ícone da bandeja
        self.tray = TrayIcon(self)
        self.tray.start()

        # Ao fechar a janela, esconde em vez de sair
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ==================== PROCESSAMENTO DE EVENTOS GLIB ====================
    def process_glib_events(self):
        """Processa eventos pendentes do GLib sem bloquear o Tkinter."""
        while GLib.main_context_default().iteration(False):
            pass
        self.root.after(10, self.process_glib_events)

    # ==================== PERSISTÊNCIA ====================
    def on_closing(self):
        """Ao fechar a janela, esconde em vez de sair."""
        self.hide_window()

    # ==================== MÉTODOS D-BUS ====================
    @dbus.service.method('studio.transcritor')
    def toggle_recording(self):
        print("🔵 D-BUS: toggle_recording chamado")
        if self.is_deepseek_focused():
            print("⏸️ Janela DeepSeek em foco, ignorando toggle_recording")
            return
        dbus_queue.put(('toggle_recording',))

    @dbus.service.method('studio.transcritor')
    def cmd_translate(self):
        print("🔵 D-BUS: cmd_translate chamado")
        dbus_queue.put(('cmd_translate',))

    @dbus.service.method('studio.transcritor')
    def cmd_save(self):
        print("🔵 D-BUS: cmd_save chamado")
        dbus_queue.put(('cmd_save',))

    @dbus.service.method('studio.transcritor')
    def cmd_correct(self):
        print("🔵 D-BUS: cmd_correct chamado")
        dbus_queue.put(('cmd_correct',))

    @dbus.service.method('studio.transcritor')
    def open_deepseek_window(self):
        print("🔵 D-BUS: open_deepseek_window chamado")
        dbus_queue.put(('open_deepseek_window',))

    # ==================== PROCESSAMENTO DA FILA ====================
    def check_dbus_queue(self):
        try:
            while True:
                cmd = dbus_queue.get_nowait()
                print(f"🟢 Fila: comando recebido = {cmd[0]}")
                try:
                    if cmd[0] == 'toggle_recording':
                        self._toggle_recording()
                    elif cmd[0] == 'cmd_translate':
                        self.translate_text_action()
                    elif cmd[0] == 'cmd_save':
                        self.save_transcription_action()
                    elif cmd[0] == 'cmd_correct':
                        self.correct_transcription_action()
                    elif cmd[0] == 'open_deepseek_window':
                        self.open_deepseek_window_action()
                    else:
                        print(f"⚠️ Comando desconhecido: {cmd[0]}")
                except Exception as e:
                    print(f"❌ Erro ao processar comando {cmd[0]}: {e}")
                    traceback.print_exc()
        except queue.Empty:
            pass
        self.root.after(100, self.check_dbus_queue)

    def _toggle_recording(self):
        print("🟠 Executando _toggle_recording")
        if self.busy:
            print("⏳ Ocupado, ignorando comando")
            return
        self.busy = True
        try:
            if not self.is_recording:
                self.start_recording()
            else:
                self.stop_and_transcribe()
        finally:
            self.busy = False

    def translate_text_action(self):
        print("🟠 Executando translate_text_action")
        self.translate_text()

    def save_transcription_action(self):
        print("🟠 Executando save_transcription_action")
        self.save_transcription()

    def correct_transcription_action(self):
        print("🟠 Executando correct_transcription_action")
        self.correct_transcription()

    # ==================== AÇÃO DE ABRIR DEEPSEEK (implementação correta) ====================
    def open_deepseek_window_action(self):
        print("🔵 open_deepseek_window_action chamado (interface)")
        # Se a janela principal não estiver visível (minimizada), entra em modo background
        if not self.root.winfo_viewable():
            if self.background_recording:
                self.stop_background_recording()
            else:
                self.start_background_recording()
        else:
            # Verifica se a janela DeepSeek já existe
            if self.deepseek_window and self.deepseek_window.window and self.deepseek_window.window.winfo_exists():
                # Se existe, traz para frente
                self.deepseek_window.window.deiconify()
                self.deepseek_window.window.lift()
                self.deepseek_window.window.focus_force()
            else:
                # Caso contrário, cria uma nova
                try:
                    self.deepseek_window = DeepSeekWindow(self.root, self)
                except Exception as e:
                    print(f"❌ Erro ao abrir DeepSeekWindow: {e}")
                    traceback.print_exc()
                    messagebox.showerror("Erro", f"Não foi possível abrir a janela DeepSeek:\n{e}")

    def is_deepseek_focused(self):
        if self.deepseek_window and self.deepseek_window.window and self.deepseek_window.window.winfo_exists():
            focused = self.deepseek_window.window.focus_get() is not None
            return focused
        return False

    # ==================== GRAVAÇÃO EM BACKGROUND (SUPER+0) ====================
    def start_background_recording(self):
        if self.background_recording:
            return
        self.background_recording = True
        self.background_audio_buffer = []
        self.background_recorder = AudioRecorder(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            callback=self.on_background_audio_chunk
        )
        self.background_recorder.start()
        self.show_notification("🎤 Gravação iniciada", "Fale agora. Pressione Super+0 novamente para parar.")
        self.reset_silence_timer()

    def stop_background_recording(self, from_timer=False):
        if not self.background_recording:
            return
        self.background_recording = False
        if self.background_timer:
            self.background_timer.cancel()
            self.background_timer = None
        audio = self.background_recorder.stop()
        if audio.size == 0:
            if from_timer:
                self.show_notification("Nada gravado", "Tempo limite de silêncio atingido.")
            else:
                self.show_notification("Nada gravado", "Nenhum áudio detectado.")
            return
        self.show_notification("⏳ Processando", "Transcrevendo e consultando DeepSeek...")
        self.process_background_audio(audio)

    def on_background_audio_chunk(self, chunk):
        self.reset_silence_timer()

    def reset_silence_timer(self):
        if self.background_timer:
            self.background_timer.cancel()
        self.background_timer = threading.Timer(5.0, lambda: self.stop_background_recording(from_timer=True))
        self.background_timer.start()

    def process_background_audio(self, audio):
        if self.transcriber is None:
            if not self.load_model():
                return
        def task():
            try:
                text = self.transcriber.transcribe(audio, language=self.current_language.get())
                if text.startswith("[Erro:") or text.startswith("❌") or "áudio muito baixo" in text.lower():
                    self.root.after(0, lambda: messagebox.showerror("Erro na transcrição", text))
                    return
                if self.deepseek_client is None:
                    try:
                        self.deepseek_client = DeepSeekClient()
                    except Exception as e:
                        self.show_notification("Erro", f"Falha ao configurar DeepSeek: {e}")
                        return
                resposta = self.deepseek_client.ask(text, opt_out=True)
                self.root.after(0, lambda: self.handle_background_response(text, resposta))
            except Exception as e:
                self.root.after(0, lambda: self.show_notification("Erro", f"Falha no processamento: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def handle_background_response(self, prompt, resposta):
        if len(resposta) < 300 and '```' not in resposta and '    ' not in resposta:
            self.show_notification("Resposta do DeepSeek", resposta[:200] + ("..." if len(resposta)>200 else ""))
            threading.Thread(target=self._speak_response, args=(resposta,), daemon=True).start()
        else:
            try:
                self.deepseek_window = DeepSeekWindow(self.root, self, initial_prompt=prompt, initial_response=resposta)
            except Exception as e:
                print(f"❌ Erro ao abrir DeepSeekWindow: {e}")
                traceback.print_exc()
                messagebox.showerror("Erro", f"Não foi possível abrir a janela DeepSeek:\n{e}")

    # ==================== VOCALIZAÇÃO ====================
    def _speak_response(self, text):
        file_path = self.tts_engine.synthesize(text, language=self.current_language.get())
        if file_path:
            self.tts_engine.play_audio(file_path)

    # ==================== LIMPEZA DE MEMÓRIA GPU ====================
    def unload_models(self):
        if self.transcriber:
            print("Descarregando transcriber...")
            del self.transcriber
            self.transcriber = None
        if self.translator:
            print("Descarregando tradutor...")
            self.translator.unload()
            del self.translator
            self.translator = None
        if self.tts_engine:
            self.tts_engine.unload_model()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("Memória GPU liberada.")

    def load_model(self):
        if self.transcriber is not None and self.transcriber.model_size != self.model_size.get():
            print("Tamanho de modelo alterado, descarregando anterior...")
            del self.transcriber
            self.transcriber = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        if self.transcriber is not None:
            return True
        try:
            self.status_var.set(f"⏳ Carregando modelo {self.model_size.get()}...")
            self.transcriber = TranscriberGPU(
                model_size=self.model_size.get(),
                device=self.device.get()
            )
            self.status_var.set(f"✅ Modelo {self.model_size.get()} carregado.")
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar modelo: {e}")
            return False

    # ==================== BANDEJA E NOTIFICAÇÕES ====================
    def hide_window(self):
        self.root.withdraw()
        self.show_notification("Aplicativo minimizado", "O programa continua em segundo plano.")

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        if self.deepseek_window and self.deepseek_window.window and self.deepseek_window.window.winfo_exists():
            self.deepseek_window.window.deiconify()
            self.deepseek_window.window.lift()
            self.deepseek_window.window.focus_force()

    def quit_app(self):
        print("Encerrando aplicativo...")
        config_dict = {
            "model_size": self.model_size.get(),
            "device": self.device.get(),
            "source_language": self.current_language.get(),
            "target_language": self.translate_target.get()
        }
        save_config(config_dict)
        self.unload_models()
        self.tray.stop()
        self.root.quit()
        sys.exit(0)

    def show_notification(self, title, message):
        try:
            subprocess.run(['notify-send', title, message])
        except Exception as e:
            print(f"Erro ao enviar notificação: {e}")

    # ==================== INTERFACE ====================
    def setup_ui(self):
        control_frame = ttk.LabelFrame(self.root, text="⚡ CONTROLES", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        # Linha 0: Modelo, idioma de origem, idioma de destino
        ttk.Label(control_frame, text="Modelo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        model_combo = tb.Combobox(control_frame, textvariable=self.model_size,
                                   values=["tiny", "base", "small", "medium", "large"],
                                   state="readonly", width=8)
        model_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ToolTip(model_combo, "Modelo Whisper a ser usado para transcrição")

        ttk.Label(control_frame, text="Idioma (origem):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        lang_combo = tb.Combobox(control_frame, textvariable=self.current_language,
                                   values=list(config.LANGUAGES.keys()),
                                   state="readonly", width=8)
        lang_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ToolTip(lang_combo, "Idioma do áudio (para transcrição)")

        ttk.Label(control_frame, text="Traduzir para:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        target_combo = tb.Combobox(control_frame, textvariable=self.translate_target,
                                     values=self.all_languages,
                                     state="readonly", width=8)
        target_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ToolTip(target_combo, "Idioma de destino para tradução")

        # Linha 1: Dispositivo e botões principais
        ttk.Label(control_frame, text="Dispositivo:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        device_combo = tb.Combobox(control_frame, textvariable=self.device,
                                     values=["cpu", "cuda"],
                                     state="readonly", width=8)
        device_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ToolTip(device_combo, "Dispositivo para inferência (GPU recomendada)")

        # Botão único de gravação (toggle)
        self.btn_record = ttk.Button(control_frame, text="▶ Gravar",
                                      style="Pink.TButton", width=20, command=self.toggle_recording)
        self.btn_record.grid(row=0, column=2, padx=5, pady=5)
        ToolTip(self.btn_record, "Iniciar/parar gravação (Super+1)")

        # Botão Traduzir com ícone
        self.btn_translate = ttk.Button(control_frame, text="🌐 Traduzir",
                                        style="Magenta.TButton", width=20, command=self.translate_text)
        self.btn_translate.grid(row=1, column=2, padx=5, pady=5)
        ToolTip(self.btn_translate, "Traduzir transcrição para o idioma selecionado (Super+2)")

        # Botão MultiTradução com ícone
        self.btn_translate_all = ttk.Button(control_frame, text="🌍 MultiTradução",
                                            style="Magenta.TButton", width=20, command=self.translate_all)
        self.btn_translate_all.grid(row=1, column=3, padx=5, pady=5)
        ToolTip(self.btn_translate_all, "Traduzir transcrição para todos os idiomas")

        # Linha 2: Botões secundários
        # Botão Salvar com ícone
        self.btn_save = ttk.Button(control_frame, text="💾 Salvar",
                                   style="Cyan.TButton", width=20, command=self.save_transcription)
        self.btn_save.grid(row=0, column=3, padx=5, pady=5)
        ToolTip(self.btn_save, "Salvar transcrição atual em arquivo (Super+3)")

        # Botão DeepSeek com ícone
        self.btn_deepseek = ttk.Button(control_frame, text="🤖 DeepSeek",
                                       style="Cyan.TButton", width=20, command=self.open_deepseek_window_action)
        self.btn_deepseek.grid(row=2, column=2, padx=5, pady=5)
        ToolTip(self.btn_deepseek, "Abrir/restaurar janela de consulta DeepSeek (Super+5)")

        # Indicador de gravação (abaixo dos controles)
        self.rec_indicator = tk.Label(self.root, text="⏹ PARADO",
                                      bg="#404040", fg="#888888",
                                      font=("Arial", 16, "bold"), pady=10)
        self.rec_indicator.pack(fill="x", padx=10, pady=5)
        ToolTip(self.rec_indicator, "Status da gravação")

        # ========== ÁREA DE TRANSCRIÇÃO ==========
        text_frame = ttk.LabelFrame(self.root, text="📝 TRANSCRIÇÃO", padding=10)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=("Consolas", 11),
                                                    bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                                                    height=8)
        self.trans_toolbar = FormatToolbar(text_frame, self.text_area, self)
        self.trans_toolbar.pack(fill="x", pady=(0,5))
        self.text_area.pack(fill="both", expand=True)

        btn_frame_trans = ttk.Frame(text_frame)
        btn_frame_trans.pack(fill="x", pady=5)
        ttk.Button(btn_frame_trans, text="✍️ Corrigir Transcrição",
                   style="Cyan.TButton", command=self.correct_transcription).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_trans, text="🗑️ Limpar",
                   style="secondary", command=lambda: self.text_area.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)

        # ========== ÁREA DE TRADUÇÕES ==========
        trans_frame = ttk.LabelFrame(self.root, text="🌐 TRADUÇÕES", padding=10)
        trans_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.trans_area = scrolledtext.ScrolledText(trans_frame, wrap=tk.WORD, font=("Consolas", 11),
                                                     bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                                                     height=8)
        self.resp_toolbar = FormatToolbar(trans_frame, self.trans_area, self)
        self.resp_toolbar.pack(fill="x", pady=(0,5))
        self.trans_area.pack(fill="both", expand=True)

        btn_frame_resp = ttk.Frame(trans_frame)
        btn_frame_resp.pack(fill="x", pady=5)
        ttk.Button(btn_frame_resp, text="✍️ Corrigir Resposta",
                   style="Cyan.TButton", command=self.correct_translation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_resp, text="🗑️ Limpar",
                   style="secondary", command=lambda: self.trans_area.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_resp, text="💾 Salvar Traduções",
                   style="Cyan.TButton", command=self.save_translations).pack(side=tk.LEFT, padx=5)

        # ========== CONFIGURAÇÃO DAS TAGS ==========
        self._configure_tags()

        # ========== STATUS BAR ==========
        self.status_var = tk.StringVar()
        self.status_var.set("✅ Pronto.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)
        ToolTip(status_bar, "Barra de status")

    def _configure_tags(self):
        base_font = tkfont.Font(font=self.text_area.cget("font"))
        family = base_font.actual()["family"]
        size = base_font.actual()["size"]
        bold_font = (family, size, "bold")
        italic_font = (family, size, "italic")
        heading_font = (family, size+4, "bold")

        for widget in [self.text_area, self.trans_area]:
            widget.tag_configure("bold", font=bold_font)
            widget.tag_configure("italic", font=italic_font)
            widget.tag_configure("underline", underline=True)
            widget.tag_configure("overstrike", overstrike=True)
            widget.tag_configure("heading", font=heading_font)
            for cor in ["red", "blue", "green", "orange", "purple", "brown"]:
                widget.tag_configure(cor, foreground=cor)

    def setup_bindings(self):
        self.text_area.bind("<Return>", lambda e: handle_enter(e, self.text_area, self))
        self.trans_area.bind("<Return>", lambda e: handle_enter(e, self.trans_area, self))

    def check_microphone(self):
        import sounddevice as sd
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d["max_input_channels"] > 0]
            if not input_devices:
                messagebox.showerror("Erro", "Nenhum dispositivo de entrada de áudio encontrado.")
            else:
                self.status_var.set(f"🎤 Microfone OK. {len(input_devices)} dispositivo(s)")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao acessar microfone: {e}")

    def start_recording(self):
        if not self.load_model():
            return
        self.recorder = AudioRecorder(samplerate=config.SAMPLE_RATE, channels=config.CHANNELS)
        self.text_area.delete(1.0, tk.END)
        self.trans_area.delete(1.0, tk.END)
        self.is_recording = True
        self.recorder.start()
        self.btn_record.config(text="⏹ PARAR GRAVAÇÃO", style="success.TButton")
        self.btn_deepseek.config(state="disabled")
        self.rec_indicator.config(text="🔴 GRAVANDO...", bg="#8b0000", fg="white")
        self.status_var.set("🔴 Gravando...")

    def stop_and_transcribe(self):
        self.is_recording = False
        audio = self.recorder.stop()
        self.btn_record.config(text="▶ INICIAR GRAVAÇÃO", style="Pink.TButton")
        self.rec_indicator.config(text="⏹ PARADO", bg="#404040", fg="#888888")
        self.status_var.set("⏳ Transcrevendo...")

        if audio.size == 0:
            messagebox.showwarning("Aviso", "Nenhum áudio gravado.")
            self.status_var.set("⚠️ Nada gravado.")
            return

        def transcribe_task():
            try:
                text = self.transcriber.transcribe(audio, language=self.current_language.get())
                if text.startswith("[Erro:") or text.startswith("❌") or "áudio muito baixo" in text.lower():
                    self.root.after(0, lambda: messagebox.showerror("Erro na transcrição", text))
                    return
                self.root.after(0, lambda: self.display_transcription(text))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na transcrição: {e}"))
                self.root.after(0, lambda: self.status_var.set("❌ Erro na transcrição."))

        threading.Thread(target=transcribe_task, daemon=True).start()

    def display_transcription(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.status_var.set("✅ Transcrição concluída.")
        self.btn_deepseek.config(state="normal")
        self.show_notification("Transcrição concluída", "O áudio foi transcrito.")

    def correct_transcription(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "Nada para corrigir.")
            return
        show_correction_dialog(self.root, "Correção da Transcrição", text,
                               lambda new: self.text_area.delete(1.0, tk.END) or self.text_area.insert(tk.END, new),
                               self.current_language.get())

    def correct_translation(self):
        text = self.trans_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "Nada para corrigir.")
            return
        show_correction_dialog(self.root, "Correção da Resposta", text,
                               lambda new: self.trans_area.delete(1.0, tk.END) or self.trans_area.insert(tk.END, new),
                               "en")

    # ---------- Métodos de tradução ----------
    def insert_translation(self, lang_name, text):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{lang_name}] "

        color_map = {
            "Inglês": "blue", "Espanhol": "red", "Francês": "green",
            "Alemão": "orange", "Italiano": "purple", "Chinês": "brown",
            "Japonês": "darkred", "Coreano": "darkgreen"
        }
        cor = color_map.get(lang_name, "white")
        tag_name = f"lang_{lang_name}"
        try:
            self.trans_area.tag_configure(tag_name, foreground=cor)
        except:
            pass

        start = self.trans_area.index("end-1c")
        self.trans_area.insert(tk.END, prefix + text + "\n\n")
        end = self.trans_area.index("end-1c")
        self.trans_area.tag_add(tag_name, start, end)
        self.trans_area.see(tk.END)

    def translate_text(self):
        print("🔵 translate_text chamado (interface)")
        text = self.text_area.get(1.0, tk.END).strip()
        print(f"🔵 Texto a traduzir: '{text}'")
        if not text:
            messagebox.showinfo("Info", "Nada para traduzir.")
            return
        self.status_var.set("⏳ Traduzindo...")
        self.root.update()
        target = self.translate_target.get()
        lang_name = self.all_language_names.get(target, target.upper())
        print(f"🔵 Idioma destino: {target} ({lang_name})")

        def task():
            try:
                print("🟠 Iniciando thread de tradução (Hunyuan)")
                if self.translator is None or self.translator.target_lang != target:
                    self.translator = Translator(
                        source_lang=self.current_language.get(),
                        target_lang=target,
                        device=self.device.get()
                    )
                translated = self.translator.translate(text)
                print(f"🟠 Tradução obtida: '{translated}'")
                self.root.after(0, lambda: self.insert_translation(lang_name, translated))
                self.root.after(0, lambda: self.status_var.set("✅ Tradução concluída."))
            except Exception as e:
                print(f"❌ Erro na thread de tradução: {e}")
                traceback.print_exc()
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na tradução: {e}"))
                self.root.after(0, lambda: self.status_var.set("❌ Erro na tradução."))

        threading.Thread(target=task, daemon=True).start()

    def translate_all(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "Nada para traduzir.")
            return
        self.status_var.set("⏳ Traduzindo para todos...")
        self.root.update()
        source = self.current_language.get()
        targets = self.all_languages

        def task():
            for target in targets:
                try:
                    translator = Translator(
                        source_lang=source,
                        target_lang=target,
                        device=self.device.get()
                    )
                    translated = translator.translate(text)
                    lang_name = self.all_language_names.get(target, target.upper())
                    self.root.after(0, lambda l=lang_name, t=translated: self.insert_translation(l, t))
                except Exception as e:
                    self.root.after(0, lambda: self.insert_translation(f"Erro ({target})", str(e)))
            self.root.after(0, lambda: self.status_var.set("✅ Traduções concluídas."))

        threading.Thread(target=task, daemon=True).start()

    # ---------- Salvar ----------
    def save_transcription(self):
        print("🔵 save_transcription chamado (interface)")
        text = self.text_area.get(1.0, tk.END).strip()
        print(f"🔵 save_transcription: texto presente? {bool(text)}")
        if not text:
            messagebox.showinfo("Info", "Nada para salvar.")
            return
        from datetime import datetime
        filename = f"transcricao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(__file__).parent.parent / "transcricoes" / filename
        filepath.parent.mkdir(exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("Sucesso", f"Transcrição salva em:\n{filepath}")

    def save_translations(self):
        print("🔵 save_translations chamado")
        text = self.trans_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "Nada para salvar.")
            return
        from datetime import datetime
        filename = f"traducoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(__file__).parent.parent / "transcricoes" / filename
        filepath.parent.mkdir(exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("Sucesso", f"Traduções salvas em:\n{filepath}")

    def __del__(self):
        self.unload_models()