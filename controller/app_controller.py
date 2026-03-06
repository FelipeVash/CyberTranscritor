# controller/app_controller.py
"""
Main application controller. Orchestrates backend services, UI updates, and D-Bus communication.
All logging is done through the centralized logger.
"""

from tkinter import ttk
import tkinter as tk
import threading
import queue
import traceback
from pathlib import Path
import sys
import torch

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from backend.models.model_manager import ModelManager
from backend.deepseek_client import DeepSeekClient
from backend.audio.recorder import AudioRecorder
from backend.audio.player import AudioPlayer
from backend.services.transcription_service import TranscriptionService, TranscriptionError
from backend.services.translation_service import TranslationService, TranslationError
from backend.services.correction_service import CorrectionService, CorrectionError
from backend.background.background_recorder import BackgroundRecorder
from frontend.deepseek_window import DeepSeekWindow
from utils.constants import ALL_LANGUAGES, ALL_LANGUAGE_NAMES
from utils.config_persistence import load_config, save_config
from utils.i18n import _, set_language, get_current_language, get_available_languages
from backend.dbus.dbus_service import DBusService
from utils.logger import logger

class AppController:
    """
    Central controller of the application.
    Manages state, coordinates services, and handles UI actions.
    """

    def __init__(self):
        """Initialize controller, load config, set up services and D-Bus."""
        logger.info("Initializing AppController")
        self.config = load_config()

        # Default values (plain strings) – Tkinter variables will be created later
        self._model_size = self.config.get("model_size", config.MODEL_SIZE)
        self._device = self.config.get("device", config.DEVICE)
        self._current_language = self.config.get("source_language", "pt")
        self._translate_target = self.config.get("target_language", "en")
        self._ui_language = self.config.get("ui_language", get_current_language())

        self.all_languages = ALL_LANGUAGES
        self.all_language_names = ALL_LANGUAGE_NAMES

        # Internal state
        self.is_recording = False
        self.recorder = None
        self.deepseek_window = None
        self.busy = False
        self._root = None

        # Services
        logger.debug("Initializing services")
        self.model_manager = ModelManager(device=self._device)
        self.deepseek_client = DeepSeekClient()
        self.audio_player = AudioPlayer()
        self.transcription_service = TranscriptionService(self.model_manager)
        self.translation_service = TranslationService(self.model_manager)
        self.correction_service = CorrectionService()
        self.background_recorder = BackgroundRecorder(self)

        # UI references (will be set later via set_ui_refs)
        self.text_area = None
        self.trans_area = None
        self.btn_record = None
        self.btn_deepseek = None
        self.rec_indicator = None
        self.status_var = None
        self.progress_bar = None

        # Tkinter variables (created in init_variables)
        self.model_size = None
        self.device = None
        self.current_language = None
        self.translate_target = None
        self.ui_language = None

        # Queue for D-Bus commands (to be processed safely in the main thread)
        self.dbus_queue = queue.Queue()

        # Start D-Bus service (passes self to access the queue)
        self.dbus_service = DBusService(self)
        logger.info("AppController initialized successfully")

    # ==================== TKINTER VARIABLES INITIALIZATION ====================

    def init_variables(self, root):
        """
        Create Tkinter variables associated with the root window.
        Must be called after the root window exists.
        """
        logger.debug("Initializing Tkinter variables")
        self._root = root
        self.model_size = tk.StringVar(root, value=self._model_size)
        self.device = tk.StringVar(root, value=self._device)
        self.current_language = tk.StringVar(root, value=self._current_language)
        self.translate_target = tk.StringVar(root, value=self._translate_target)
        self.ui_language = tk.StringVar(root, value=self._ui_language)

        # Trace language changes
        self.ui_language.trace('w', self._on_language_change)

    # ==================== PROPERTIES ====================

    @property
    def root(self):
        """Return the main tkinter root window."""
        return self._root

    @property
    def transcriber(self):
        """Lazy getter for the transcriber (loads on demand)."""
        return self.model_manager.get_transcriber(self.model_size.get())

    # ==================== UI REFERENCE SETTER ====================

    def set_ui_refs(self, text_area, trans_area, btn_record, btn_deepseek, rec_indicator, status_var, progress_bar=None):
        """Store references to UI widgets for later updates."""
        logger.debug("Setting UI references")
        self.text_area = text_area
        self.trans_area = trans_area
        self.btn_record = btn_record
        self.btn_deepseek = btn_deepseek
        self.rec_indicator = rec_indicator
        self.status_var = status_var
        self.progress_bar = progress_bar

    # ==================== PROGRESS BAR CONTROL ====================

    def start_progress(self, text=None):
        """Start the indeterminate progress bar and optionally update status text."""
        if self.progress_bar:
            self.progress_bar.pack(side=tk.BOTTOM, pady=2)
            self.progress_bar.start(10)
        if text:
            self.status_var.set(text)

    def stop_progress(self, text=None):
        """Stop and hide the progress bar, optionally update status text."""
        if self.progress_bar:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
        if text:
            self.status_var.set(text)

    # ==================== CENTRALIZED ERROR HANDLING ====================

    def _handle_service_error(self, exception, user_message_key=None, **kwargs):
        """
        Centralized error handling for service operations.

        Args:
            exception: The exception that occurred.
            user_message_key: i18n key for the message to show to the user.
            **kwargs: Additional parameters for the i18n message.
        """
        logger.error(f"Service error: {exception}", exc_info=True)
        if user_message_key:
            self.show_error(_("dialogs.common.error"), _(user_message_key, **kwargs))
        else:
            self.show_error(_("dialogs.common.error"), str(exception))

    # ==================== D-BUS QUEUE PROCESSING ====================

    def process_dbus_queue(self):
        """
        Process commands from the D-Bus queue.
        This method must be called periodically by the UI main loop.
        """
        try:
            while True:
                cmd = self.dbus_queue.get_nowait()
                logger.debug(f"Processing D-Bus command: {cmd[0]}")
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
                        logger.debug("Processing stop_audio command")
                        self.stop_all_audio()
                    elif cmd[0] == 'toggle_background':
                        self._toggle_background_action()
                except Exception as e:
                    logger.error(f"Error processing command {cmd[0]}: {e}")
                    traceback.print_exc()
        except queue.Empty:
            pass

    def _toggle_recording_action(self):
        """Toggle recording state (called from UI or D-Bus)."""
        logger.debug(f"_toggle_recording_action: busy={self.busy}, is_recording={self.is_recording}")
        if self.busy:
            logger.warning("System busy, ignoring toggle")
            return
        self.busy = True
        try:
            if not self.is_recording:
                self.start_recording()
            else:
                self.stop_and_transcribe()
        finally:
            self.busy = False

    def toggle_recording(self):
        """Public method called by the UI to toggle recording."""
        logger.debug("toggle_recording called from UI")
        self._toggle_recording_action()

    def _toggle_background_action(self):
        """Toggle background recording mode."""
        if self.background_recorder.recording:
            logger.info("Stopping background recording")
            self.background_recorder.stop()
        else:
            logger.info("Starting background recording")
            self.background_recorder.start()

    # ==================== LANGUAGE CHANGE ====================

    def _on_language_change(self, *args):
        """Callback triggered when UI language is changed."""
        selected = self.ui_language.get()
        # Extract code from parentheses, e.g. "Português (pt)" -> "pt"
        import re
        match = re.search(r'\(([^)]+)\)', selected)
        if match:
            code = match.group(1)
            logger.info(f"Changing UI language to: {code}")
            set_language(code)
            self.update_ui_language()
        else:
            logger.error(f"Invalid language format: {selected}")

    def update_ui_language(self):
        """Update all UI texts to the current language."""
        logger.debug("Updating UI language")
        if self.root:
            self._update_widget_language(self.root)
        if self.deepseek_window and self.deepseek_window.window.winfo_exists():
            self._update_widget_language(self.deepseek_window.window)

    def _update_widget_language(self, widget):
        """Recursively update text of widgets that have an i18n_key attribute."""
        if hasattr(widget, 'i18n_key') and widget.i18n_key:
            try:
                new_text = _(widget.i18n_key)
                if isinstance(widget, (ttk.Label, ttk.Button, ttk.Checkbutton,
                                       ttk.Radiobutton, ttk.Menubutton, ttk.LabelFrame,
                                       tk.Label, tk.Button, tk.Checkbutton, tk.Radiobutton)):
                    widget.config(text=new_text)
            except Exception as e:
                logger.error(f"Error updating widget {widget}: {e}")
        for child in widget.winfo_children():
            self._update_widget_language(child)

    def get_ui_language_options(self):
        """Return list of language options for the combobox (name + code)."""
        codes = get_available_languages()
        options = []
        for code in codes:
            name = _("common.languages." + code)
            options.append(f"{name} ({code})")
        return options

    # ==================== MAIN ACTIONS ====================

    def start_recording(self):
        """Start audio recording."""
        logger.info("Starting recording")
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
        """Stop recording and start transcription in a thread."""
        logger.info("Stopping recording and transcribing")
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
                self.root.after(0, lambda: self._handle_service_error(e, e.key, **e.kwargs))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))
            except Exception as e:
                self.root.after(0, lambda: self._handle_service_error(e))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))

        threading.Thread(target=transcribe_task, daemon=True).start()

    def display_transcription(self, text):
        """Display transcribed text in the UI."""
        logger.info("Transcription completed")
        self.text_area.insert(tk.END, text + "\n")
        self.stop_progress(_("main_window.status.transcribing_done"))
        self.btn_deepseek.config(state="normal")
        self.show_notification(_("tray.notifications.transcription_ready"), "")

    def translate_text(self):
        """Translate the current transcription."""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        logger.info("Starting translation")
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
                self.root.after(0, lambda: self._handle_service_error(e, e.key, **e.kwargs))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))
            except Exception as e:
                self.root.after(0, lambda: self._handle_service_error(e))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))

        threading.Thread(target=task, daemon=True).start()

    def translate_all(self):
        """Translate to all supported languages except the source language."""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        logger.info("Starting multi-language translation")
        self.start_progress(_("main_window.status.translating"))
        source = self.current_language.get()
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
                except TranslationError as e:
                    logger.error(f"Translation error for {target}: {e}")
                    self.root.after(0, lambda: self.insert_translation(target, f"[Error: {e}]"))
                except Exception as e:
                    logger.error(f"Unexpected error for {target}: {e}")
                    self.root.after(0, lambda: self.insert_translation(target, f"[Error: {e}]"))
            self.root.after(0, lambda: self.stop_progress(_("main_window.status.translating_done")))

        threading.Thread(target=task, daemon=True).start()

    def insert_translation(self, lang_code, text):
        """Insert a translation into the translations area with language code in brackets."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{lang_code.upper()}] "
        self.trans_area.insert(tk.END, prefix)
        self.trans_area.insert(tk.END, text + "\n\n")
        self.trans_area.see(tk.END)

    def correct_transcription(self):
        """Open correction dialog for the transcription text."""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        logger.debug("Opening transcription correction dialog")
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
        """Open correction dialog for the translation area (target language: English)."""
        text = self.trans_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        logger.debug("Opening translation correction dialog")
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
        """Save the current transcription to a file."""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        from datetime import datetime
        filename = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(__file__).parent.parent / "transcriptions" / filename
        filepath.parent.mkdir(exist_ok=True)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"Transcription saved to {filepath}")
            self.show_info(_("dialogs.common.success"), _("main_window.status.saved", filename=filename))
        except Exception as e:
            logger.error(f"Failed to save transcription: {e}")
            self.show_error(_("dialogs.common.error"), str(e))

    def save_translations(self):
        """Save all translations to a file."""
        text = self.trans_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        from datetime import datetime
        filename = f"translations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(__file__).parent.parent / "transcriptions" / filename
        filepath.parent.mkdir(exist_ok=True)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"Translations saved to {filepath}")
            self.show_info(_("dialogs.common.success"), _("main_window.status.saved", filename=filename))
        except Exception as e:
            logger.error(f"Failed to save translations: {e}")
            self.show_error(_("dialogs.common.error"), str(e))

    def open_deepseek_window(self):
        """Open or restore the DeepSeek query window."""
        if self.deepseek_window and self.deepseek_window.window.winfo_exists():
            logger.debug("Restoring existing DeepSeek window")
            self.deepseek_window.show_window()
        else:
            logger.info("Creating new DeepSeek window")
            try:
                self.deepseek_window = DeepSeekWindow(
                    self.root,
                    self,
                    audio_player=self.audio_player
                )
            except Exception as e:
                self._handle_service_error(e, "deepseek_window.messages.deepseek_error", error=str(e))

    def open_deepseek_with_context(self, prompt, response):
        """Open DeepSeek window with a pre-filled prompt and response."""
        if self.deepseek_window and self.deepseek_window.window.winfo_exists():
            logger.debug("Closing existing DeepSeek window to open with context")
            self.deepseek_window.destroy()
        try:
            logger.info("Opening DeepSeek window with context")
            self.deepseek_window = DeepSeekWindow(
                self.root,
                self,
                initial_prompt=prompt,
                initial_response=response,
                audio_player=self.audio_player
            )
        except Exception as e:
            self._handle_service_error(e, "deepseek_window.messages.deepseek_error", error=str(e))

    def stop_all_audio(self):
        """Stop all audio playback."""
        logger.info("Stopping all audio")
        self.audio_player.stop()

    # ==================== BACKGROUND RECORDING (already integrated) ====================

    # ==================== NOTIFICATIONS AND DIALOGS ====================

    def show_notification(self, title, message):
        """Send a desktop notification."""
        try:
            import subprocess
            subprocess.run(['notify-send', title, message])
            logger.debug(f"Notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def show_error(self, title, message):
        """Show an error message box."""
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self.root)

    def show_info(self, title, message):
        """Show an information message box."""
        from tkinter import messagebox
        messagebox.showinfo(title, message, parent=self.root)

    def show_warning(self, title, message):
        """Show a warning message box."""
        from tkinter import messagebox
        messagebox.showwarning(title, message, parent=self.root)

    # ==================== APPLICATION SHUTDOWN ====================

    def quit_app(self):
        """Shut down the application, save config, unload models."""
        logger.info("Shutting down application")
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
        logger.info("Application terminated")
        sys.exit(0)