# controller/app_controller.py
from tkinter import ttk
import tkinter as tk
import threading
import queue
import traceback
from pathlib import Path
import sys
import torch
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from backend.models.model_manager import ModelManager
from backend.deepseek_client import DeepSeekClient
from backend.audio.recorder import AudioRecorder
from backend.audio.player import AudioPlayer
from backend.services.transcription_service import TranscriptionService, TranscriptionError
from backend.services.translation_service import TranslationService, TranslationError
from backend.services.correction_service import CorrectionService
from backend.background.background_recorder import BackgroundRecorder
from frontend.deepseek_window import DeepSeekWindow
from utils.constants import ALL_LANGUAGES, ALL_LANGUAGE_NAMES
from utils.config_persistence import load_config, save_config
from utils.i18n import _, set_language, get_current_language, get_available_languages

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class AppController(dbus.service.Object):
    def __init__(self):
        # Inicializa D-Bus
        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName('studio.transcritor', bus)
        dbus.service.Object.__init__(self, bus_name, '/studio/transcritor')

        self.config = load_config()
        
        # Valores padrão (strings comuns) - não criar StringVar aqui
        self._model_size = self.config.get("model_size", config.MODEL_SIZE)
        self._device = self.config.get("device", config.DEVICE)
        self._current_language = self.config.get("source_language", "pt")
        self._translate_target = self.config.get("target_language", "en")
        self._ui_language = self.config.get("ui_language", get_current_language())

        self.all_languages = ALL_LANGUAGES
        self.all_language_names = ALL_LANGUAGE_NAMES

        self.is_recording = False
        self.recorder = None
        self.deepseek_window = None
        self.busy = False
        self._root = None

        # Serviços
        self.model_manager = ModelManager(device=self._device)
        self.deepseek_client = DeepSeekClient()
        self.audio_player = AudioPlayer()
        self.transcription_service = TranscriptionService(self.model_manager)
        self.translation_service = TranslationService(self.model_manager)
        self.correction_service = CorrectionService()
        self.background_recorder = BackgroundRecorder(self)

        # Referências da UI
        self.text_area = None
        self.trans_area = None
        self.btn_record = None
        self.btn_deepseek = None
        self.rec_indicator = None
        self.status_var = None
        self.progress_bar = None

        # Variáveis Tkinter (serão criadas em init_variables)
        self.model_size = None
        self.device = None
        self.current_language = None
        self.translate_target = None
        self.ui_language = None

        self.dbus_queue = queue.Queue()
        print("✅ Controller D-Bus registrado")

    # ==================== INICIALIZAÇÃO DAS VARIÁVEIS TKINTER ====================
    def init_variables(self, root):
        """Cria as variáveis Tkinter associadas à janela raiz."""
        self._root = root
        self.model_size = tk.StringVar(root, value=self._model_size)
        self.device = tk.StringVar(root, value=self._device)
        self.current_language = tk.StringVar(root, value=self._current_language)
        self.translate_target = tk.StringVar(root, value=self._translate_target)
        self.ui_language = tk.StringVar(root, value=self._ui_language)

        # Configura trace para mudança de idioma
        self.ui_language.trace('w', self._on_language_change)

    # ==================== PROPRIEDADES ====================
    @property
    def root(self):
        return self._root

    @property
    def transcriber(self):
        return self.model_manager.get_transcriber(self.model_size.get())

    # ==================== VINCULAÇÃO COM UI ====================
    def set_ui_refs(self, text_area, trans_area, btn_record, btn_deepseek, rec_indicator, status_var, progress_bar=None):
        self.text_area = text_area
        self.trans_area = trans_area
        self.btn_record = btn_record
        self.btn_deepseek = btn_deepseek
        self.rec_indicator = rec_indicator
        self.status_var = status_var
        self.progress_bar = progress_bar

    # ==================== CONTROLE DE PROGRESSO ====================
    def start_progress(self, text=None):
        """Inicia a barra de progresso indeterminada e opcionalmente atualiza status."""
        if self.progress_bar:
            self.progress_bar.pack(side=tk.BOTTOM, pady=2)
            self.progress_bar.start(10)
        if text:
            self.status_var.set(text)

    def stop_progress(self, text=None):
        """Para a barra de progresso e esconde."""
        if self.progress_bar:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
        if text:
            self.status_var.set(text)

    # ==================== MÉTODOS D-BUS ====================
    @dbus.service.method('studio.transcritor')
    def toggle_recording(self):
        print("🔵 D-BUS: toggle_recording chamado")
        self.dbus_queue.put(('toggle_recording',))

    @dbus.service.method('studio.transcritor')
    def translate(self):
        print("🔵 D-BUS: translate chamado")
        self.dbus_queue.put(('translate',))

    @dbus.service.method('studio.transcritor')
    def save(self):
        print("🔵 D-BUS: save chamado")
        self.dbus_queue.put(('save',))

    @dbus.service.method('studio.transcritor')
    def correct(self):
        print("🔵 D-BUS: correct chamado")
        self.dbus_queue.put(('correct',))

    @dbus.service.method('studio.transcritor')
    def open_deepseek(self):
        print("🔵 D-BUS: open_deepseek chamado")
        self.dbus_queue.put(('open_deepseek',))

    @dbus.service.method('studio.transcritor')
    def stop_audio(self):
        print("🔵 D-BUS: stop_audio chamado")
        self.dbus_queue.put(('stop_audio',))

    # ==================== PROCESSAMENTO DA FILA ====================
    def process_dbus_queue(self):
        try:
            while True:
                cmd = self.dbus_queue.get_nowait()
                print(f"🟢 Controller: comando recebido = {cmd[0]}")
                try:
                    if cmd[0] == 'toggle_recording':
                        self._toggle_recording_action()
                    elif cmd[0] == 'translate':
                        self.translate_text()
                    elif cmd[0] == 'save':
                        self.save_transcription()
                    elif cmd[0] == 'correct':
                        self.correct_transcription()
                    elif cmd[0] == 'open_deepseek':
                        self.open_deepseek_window()
                    elif cmd[0] == 'stop_audio':
                        print("🟢 Processando stop_audio da fila")
                        self.stop_all_audio()
                except Exception as e:
                    print(f"❌ Erro ao processar comando {cmd[0]}: {e}")
                    traceback.print_exc()
        except queue.Empty:
            pass

    def _toggle_recording_action(self):
        if self.busy:
            return
        self.busy = True
        try:
            if not self.is_recording:
                self.start_recording()
            else:
                self.stop_and_transcribe()
        finally:
            self.busy = False

    # ==================== MUDANÇA DE IDIOMA ====================
    def _on_language_change(self, *args):
        selected = self.ui_language.get()
        # Extrai o código entre parênteses (ex: "Português (pt)" -> "pt")
        import re
        match = re.search(r'\(([^)]+)\)', selected)
        if match:
            code = match.group(1)
            set_language(code)
            self.update_ui_language()
        else:
            print("Formato inválido para idioma")

    def update_ui_language(self):
        """Atualiza todos os textos da interface para o idioma atual."""
        if self.root:
            self._update_widget_language(self.root)
        if self.deepseek_window and self.deepseek_window.window.winfo_exists():
            self._update_widget_language(self.deepseek_window.window)

    def _update_widget_language(self, widget):
        """Atualiza recursivamente os textos dos widgets que possuem i18n_key."""
        if hasattr(widget, 'i18n_key') and widget.i18n_key:
            try:
                new_text = _(widget.i18n_key)
                if isinstance(widget, (ttk.Label, ttk.Button, ttk.Checkbutton,
                                       ttk.Radiobutton, ttk.Menubutton, ttk.LabelFrame,
                                       tk.Label, tk.Button, tk.Checkbutton, tk.Radiobutton)):
                    widget.config(text=new_text)
            except Exception as e:
                print(f"Erro ao atualizar widget {widget}: {e}")
        for child in widget.winfo_children():
            self._update_widget_language(child)

    def get_ui_language_options(self):
        """Retorna lista de opções de idioma para o combobox (nome + código)."""
        codes = get_available_languages()
        options = []
        for code in codes:
            name = _("common.languages." + code)  # ex: "Português"
            options.append(f"{name} ({code})")
        return options

    # ==================== AÇÕES PRINCIPAIS ====================
    def start_recording(self):
        self.recorder = AudioRecorder(samplerate=config.SAMPLE_RATE, channels=config.CHANNELS)
        self.text_area.delete(1.0, tk.END)
        self.trans_area.delete(1.0, tk.END)
        self.is_recording = True
        self.recorder.start()
        self.btn_record.config(text=_("main_window.controls.buttons.stop_record"), style="success.TButton")
        self.btn_deepseek.config(state="disabled")
        self.rec_indicator.config(text=_("main_window.indicators.recording"), bg="#8b0000", fg="white")
        self.status_var.set(_("common.audio.recording"))

    def stop_and_transcribe(self):
        """Para a gravação e inicia a transcrição em thread."""
        self.is_recording = False
        audio = self.recorder.stop()
        self.btn_record.config(text=_("main_window.controls.buttons.record"), style="Pink.TButton")
        self.rec_indicator.config(text=_("main_window.indicators.stopped"), bg="#404040", fg="#888888")
        self.status_var.set(_("main_window.status.transcribing"))
        self.start_progress(_("main_window.status.transcribing"))

        if audio.size == 0:
            self.show_warning(_("dialogs.common.warning"), _("deepseek_window.messages.no_audio"))
            self.stop_progress(_("main_window.indicators.ready"))
            return

        def transcribe_task():
            try:
                text = self.transcription_service.transcribe(
                    audio,
                    language=self.current_language.get(),
                    model_size=self.model_size.get()
                )
                self.root.after(0, lambda: self.display_transcription(text))
            except TranscriptionError as e:
                self.root.after(0, lambda: self.show_error(
                    _("dialogs.common.error"),
                    _(e.key, **e.kwargs)
                ))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(
                    _("dialogs.common.error"),
                    f"Erro inesperado: {e}"
                ))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))

        threading.Thread(target=transcribe_task, daemon=True).start()

    def display_transcription(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.stop_progress(_("main_window.status.transcribing_done"))
        self.btn_deepseek.config(state="normal")
        self.show_notification(_("tray.notifications.transcription_ready"), "")

    def translate_text(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        self.start_progress(_("main_window.status.translating"))
        target = self.translate_target.get()

        def task():
            try:
                translated = self.translation_service.translate(
                    text,
                    source_lang=self.current_language.get(),
                    target_lang=target
                )
                self.root.after(0, lambda: self.insert_translation(target, translated))
                self.root.after(0, lambda: self.stop_progress(_("main_window.status.translating_done")))
            except TranslationError as e:
                self.root.after(0, lambda e=e: self.show_error(
                    _("dialogs.common.error"),
                    _(e.key, **e.kwargs)
                ))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))
            except Exception as e:
                self.root.after(0, lambda e=e: self.show_error(
                    _("dialogs.common.error"),
                    str(e)
                ))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))

        threading.Thread(target=task, daemon=True).start()

    def translate_all(self):
        """Traduz para todos os idiomas suportados, exceto o idioma de origem."""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        self.start_progress(_("main_window.status.translating"))
        source = self.current_language.get()
        # Filtra a lista de idiomas excluindo o de origem
        targets = [lang for lang in self.all_languages if lang != source]

        def task():
            for target in targets:
                try:
                    translated = self.translation_service.translate(
                        text,
                        source_lang=source,
                        target_lang=target
                    )
                    self.root.after(0, lambda l=target, t=translated: self.insert_translation(l, t))
                except Exception as e:
                    self.root.after(0, lambda: self.insert_translation(target, f"[Erro: {e}]"))
            self.root.after(0, lambda: self.stop_progress(_("main_window.status.translating_done")))

        threading.Thread(target=task, daemon=True).start()

    def insert_translation(self, lang_code, text):
        """Insere uma tradução na área de traduções com código do idioma entre colchetes."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{lang_code.upper()}] "
        # Insere sem tags especiais (usa a fonte padrão do widget)
        self.trans_area.insert(tk.END, prefix)
        self.trans_area.insert(tk.END, text + "\n\n")
        self.trans_area.see(tk.END)

    def correct_transcription(self):
        """Corrige a transcrição atual usando o serviço de correção."""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        from frontend.dialogs import show_correction_dialog
        show_correction_dialog(
            self.root,
            _("dialogs.correction.title"),
            text,
            lambda new: self.text_area.delete(1.0, tk.END) or self.text_area.insert(tk.END, new),
            self.current_language.get(),
            correction_service=self.correction_service
        )

    def correct_translation(self):
        """Corrige a tradução atual usando o serviço de correção (idioma alvo: inglês)."""
        text = self.trans_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        from frontend.dialogs import show_correction_dialog
        show_correction_dialog(
            self.root,
            _("dialogs.correction.title_response"),
            text,
            lambda new: self.trans_area.delete(1.0, tk.END) or self.trans_area.insert(tk.END, new),
            "en",
            correction_service=self.correction_service
        )

    def save_transcription(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        from datetime import datetime
        filename = f"transcricao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(__file__).parent.parent / "transcricoes" / filename
        filepath.parent.mkdir(exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        self.show_info(_("dialogs.common.success"), _("main_window.status.saved", filename=filepath))

    def save_translations(self):
        text = self.trans_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        from datetime import datetime
        filename = f"traducoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(__file__).parent.parent / "transcricoes" / filename
        filepath.parent.mkdir(exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        self.show_info(_("dialogs.common.success"), _("main_window.status.saved", filename=filepath))

    def open_deepseek_window(self):
        if self.deepseek_window and self.deepseek_window.window.winfo_exists():
            self.deepseek_window.show_window()
        else:
            try:
                self.deepseek_window = DeepSeekWindow(
                    self.root,
                    self,
                    audio_player=self.audio_player
                )
            except Exception as e:
                print(f"❌ Erro ao abrir DeepSeekWindow: {e}")
                traceback.print_exc()
                self.show_error(_("dialogs.common.error"), _("deepseek_window.messages.deepseek_error", error=str(e)))

    def stop_all_audio(self):
        print("🔇 Parando todo áudio via AudioPlayer")
        self.audio_player.stop()

    # Background recording (simplificado)
    def start_background_recording(self):
        self.background_recorder.start()

    def stop_background_recording(self, from_timer=False):
        self.background_recorder.stop(from_timer)

    def show_notification(self, title, message):
        try:
            import subprocess
            subprocess.run(['notify-send', title, message])
        except Exception as e:
            print(f"Erro na notificação: {e}")

    def show_error(self, title, message):
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self.root)

    def show_info(self, title, message):
        from tkinter import messagebox
        messagebox.showinfo(title, message, parent=self.root)

    def show_warning(self, title, message):
        from tkinter import messagebox
        messagebox.showwarning(title, message, parent=self.root)

    def quit_app(self):
        print("Encerrando aplicativo...")
        config_dict = {
            "model_size": self.model_size.get(),
            "device": self.device.get(),
            "source_language": self.current_language.get(),
            "target_language": self.translate_target.get(),
            "ui_language": self.ui_language.get()
        }
        save_config(config_dict)
        self.stop_all_audio()
        self.model_manager.unload_all()
        if self.root:
            self.root.quit()
        sys.exit(0)