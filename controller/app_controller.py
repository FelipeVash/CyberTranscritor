"""
Main application controller.
Orchestrates backend services, UI updates, and D-Bus communication.
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
import re

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
from utils.constants import ALL_LANGUAGES, ALL_LANGUAGE_NAMES, TTS_VOICES, TRANSLATION_MODELS
from utils.config_persistence import load_config, save_config, CONFIG_FILE
from utils.i18n import _, set_language, get_current_language, get_available_languages, get_language_display
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
        
        config_file_exists = CONFIG_FILE.exists()
        self.config = load_config()

        # First run: detect hardware and set recommended defaults
        if not config_file_exists:
            from utils.hardware_detector import get_recommended_settings
            rec = get_recommended_settings()
            self._device = rec["device"]
            self._model_size = rec["model_size"]
            self._translation_model = rec["translation_model"]
            self._tts_voice = rec["tts_voice"]
            self.config.update(rec)
            save_config(self.config)
            logger.info(f"First run – hardware detection applied: device={self._device}, model={self._model_size}")
        else:
            # Load from saved config
            self._device = self.config.get("device", config.DEVICE)
            self._model_size = self.config.get("model_size", config.MODEL_SIZE)
            self._translation_model = self.config.get("translation_model", "nllb-3.3B")
            self._tts_voice = self.config.get("tts_voice", "pt_BR-faber-medium")

        self._current_language = self.config.get("source_language", "pt")
        self._translate_target = self.config.get("target_language", "en")
        # Ensure UI language is stored as "Name (code)" format
        saved_ui = self.config.get("ui_language", get_language_display(get_current_language()))
        # If by any chance it's just the code, convert it
        if '(' not in saved_ui:
            saved_ui = get_language_display(saved_ui)
        self._ui_language = saved_ui
        self._idle_timeout = self.config.get("idle_timeout", 60)

        self.all_languages = ALL_LANGUAGES
        self.all_language_names = ALL_LANGUAGE_NAMES
        self.tts_voices = TTS_VOICES
        self.translation_models = TRANSLATION_MODELS

        self.is_recording = False
        self.recorder = None
        self.deepseek_window = None
        self.busy = False
        self._root = None

        logger.debug("Initializing services")
        self.model_manager = ModelManager(device=self._device, idle_timeout=self._idle_timeout)
        self.deepseek_client = DeepSeekClient()
        self.audio_player = AudioPlayer()
        self.transcription_service = TranscriptionService(self.model_manager)
        self.translation_service = TranslationService(self.model_manager)
        self.correction_service = CorrectionService()
        self.background_recorder = BackgroundRecorder(self)

        # UI references (to be set later)
        self.text_area = None
        self.trans_area = None
        self.btn_record = None
        self.btn_deepseek = None
        self.rec_indicator = None
        self.status_var = None
        self.progress_bar = None

        # Tkinter variables (to be initialized with root)
        self.model_size = None
        self.device = None
        self.current_language = None
        self.translate_target = None
        self.ui_language = None
        self.tts_voice = None
        self.translation_model = None
        self.idle_timeout = None

        self.dbus_queue = queue.Queue()
        self.dbus_service = DBusService(self)
        logger.info("AppController initialized successfully")

    def init_variables(self, root):
        """Initialize Tkinter variables with the given root window."""
        logger.debug("Initializing Tkinter variables")
        self._root = root
        self.model_size = tk.StringVar(root, value=self._model_size)
        self.device = tk.StringVar(root, value=self._device)
        self.current_language = tk.StringVar(root, value=self._current_language)
        self.translate_target = tk.StringVar(root, value=self._translate_target)
        self.ui_language = tk.StringVar(root, value=self._ui_language)
        self.tts_voice = tk.StringVar(root, value=self._tts_voice)
        self.translation_model = tk.StringVar(root, value=self._translation_model)
        self.idle_timeout = tk.StringVar(root, value=str(self._idle_timeout))

        # Trace changes to trigger actions
        self.ui_language.trace('w', self._on_language_change)
        self.tts_voice.trace('w', self._on_tts_voice_change)
        self.translation_model.trace('w', self._on_translation_model_change)
        self.idle_timeout.trace('w', self._on_idle_timeout_change)

    @property
    def root(self):
        """Return the root Tk window."""
        return self._root

    @property
    def transcriber(self):
        """Convenience property to get the current transcriber from model manager."""
        return self.model_manager.get_transcriber(self.model_size.get())

    def set_ui_refs(self, text_area, trans_area, btn_record, btn_deepseek, rec_indicator, status_var, progress_bar=None):
        """Store references to UI elements for later manipulation."""
        logger.debug("Setting UI references")
        self.text_area = text_area
        self.trans_area = trans_area
        self.btn_record = btn_record
        self.btn_deepseek = btn_deepseek
        self.rec_indicator = rec_indicator
        self.status_var = status_var
        self.progress_bar = progress_bar

    def start_progress(self, text=None):
        """Show and start the indeterminate progress bar, optionally set status text."""
        if self.progress_bar:
            self.progress_bar.pack(side=tk.BOTTOM, pady=2)
            self.progress_bar.start(10)
        if text:
            self.status_var.set(text)

    def stop_progress(self, text=None):
        """Stop and hide the progress bar, optionally set status text."""
        if self.progress_bar:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
        if text:
            self.status_var.set(text)

    def process_dbus_queue(self):
        """Process any pending D-Bus commands from the queue."""
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
        """Internal method to toggle recording, handling busy state."""
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
        """Public method called from UI to toggle recording."""
        logger.debug("toggle_recording called from UI")
        self._toggle_recording_action()

    def _toggle_background_action(self):
        """Toggle background recording on/off."""
        if self.background_recorder.recording:
            logger.info("Stopping background recording")
            self.background_recorder.stop()
        else:
            logger.info("Starting background recording")
            self.background_recorder.start()

    def _on_language_change(self, *args):
        """Handle UI language change: extract code and update i18n."""
        selected = self.ui_language.get()
        match = re.search(r'\(([^)]+)\)', selected)
        if match:
            code = match.group(1)
            logger.info(f"Changing UI language to: {code}")
            set_language(code)
            self.update_ui_language()
        else:
            logger.warning(f"Invalid language format: {selected} – using as code")
            set_language(selected)
            self.update_ui_language()

    def _on_tts_voice_change(self, *args):
        """Handle TTS voice change (logging only, actual change happens in DeepSeek window)."""
        new_voice = self.tts_voice.get()
        logger.info(f"TTS voice changed to: {new_voice}")

    def _on_translation_model_change(self, *args):
        """Handle translation model change (logging only)."""
        new_model = self.translation_model.get()
        logger.info(f"Translation model changed to: {new_model}")

    def _on_idle_timeout_change(self, *args):
        """Handle idle timeout change."""
        try:
            new_timeout = int(self.idle_timeout.get())
            logger.info(f"Idle timeout changed to: {new_timeout} seconds")
            self.model_manager.idle_timeout = new_timeout
        except ValueError:
            logger.error(f"Invalid idle timeout value: {self.idle_timeout.get()}")

    def update_ui_language(self):
        """Update all UI widgets to reflect new language."""
        logger.debug("Updating UI language")
        if self.root:
            self._update_widget_language(self.root)
        if self.deepseek_window and self.deepseek_window.window.winfo_exists():
            self._update_widget_language(self.deepseek_window.window)

    def _update_widget_language(self, widget):
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
        """Return a list of language display strings for the combobox."""
        codes = get_available_languages()
        options = []
        for code in codes:
            name = _("common.languages." + code)
            options.append(f"{name} ({code})")
        return options

    def _handle_service_error(self, exception, user_message_key=None, **kwargs):
        """Log error and show a user-friendly message box."""
        logger.error(f"Service error: {exception}", exc_info=True)
        if user_message_key:
            self.show_error(_("dialogs.common.error"), _(user_message_key, **kwargs))
        else:
            self.show_error(_("dialogs.common.error"), str(exception))

    def start_recording(self):
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
        """Stop recording and start transcription in a background thread."""
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
            """Background transcription task."""
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
        """Insert transcribed text into the text area and update UI."""
        logger.info("Transcription completed")
        self.text_area.insert(tk.END, text + "\n")
        self.stop_progress(_("main_window.status.transcribing_done"))
        self.btn_deepseek.config(state="normal")
        self.show_notification(_("tray.notifications.transcription_ready"), "")

    def translate_text(self):
        """Translate the current transcription to the target language."""
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
                self.root.after(0, lambda e=e: self._handle_service_error(e, e.key, **e.kwargs))
                self.root.after(0, lambda: self.stop_progress(_("main_window.indicators.error")))
            except Exception as e:
                self.root.after(0, lambda e=e: self._handle_service_error(e))
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
                    logger.debug(f"Translating {source} -> {target}")
                    translated = self.translation_service.translate(
                        text,
                        source_lang=source,
                        target_lang=target
                    )
                    self.root.after(0, lambda t=target, tr=translated: self.insert_translation(t, tr))
                except Exception as e:
                    logger.error(f"Translation error for {target}: {e}")
                    self.root.after(0, lambda t=target, err=e: self.insert_translation(t, f"[Error: {err}]"))
            self.root.after(0, lambda: self.stop_progress(_("main_window.status.translating_done")))

        threading.Thread(target=task, daemon=True).start()

    def insert_translation(self, lang_code, text):
        """Insert a translation with timestamp and language prefix."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{lang_code.upper()}] "
        self.trans_area.insert(tk.END, prefix)
        self.trans_area.insert(tk.END, text + "\n\n")
        self.trans_area.see(tk.END)

    def correct_transcription(self):
        """Open correction dialog for the transcription area."""
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
        """Open correction dialog for the translation area."""
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
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        from datetime import datetime
        filename = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(__file__).parent.parent / "transcriptions" / filename
        filepath.parent.mkdir(exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"Transcription saved to {filepath}")
        self.show_info(_("dialogs.common.success"), _("main_window.status.saved", filename=filename))

    def save_translations(self):
        """Save the current translations to a file."""
        text = self.trans_area.get(1.0, tk.END).strip()
        if not text:
            self.show_info(_("dialogs.common.info"), _("deepseek_window.messages.no_text"))
            return
        from datetime import datetime
        filename = f"translations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(__file__).parent.parent / "transcriptions" / filename
        filepath.parent.mkdir(exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"Translations saved to {filepath}")
        self.show_info(_("dialogs.common.success"), _("main_window.status.saved", filename=filename))

    def open_deepseek_window(self):
        """Open (or restore) the DeepSeek chat window."""
        if self.deepseek_window and self.deepseek_window.window.winfo_exists():
            logger.debug("Restoring existing DeepSeek window")
            self.deepseek_window.show_window()
        else:
            logger.info("Creating new DeepSeek window")
            try:
                self.deepseek_window = DeepSeekWindow(
                    self.root,
                    self,
                    audio_player=self.audio_player,
                    tts_voice=self.tts_voice.get() if self.tts_voice else "pt_BR-faber-medium"
                )
            except Exception as e:
                self._handle_service_error(e, "deepseek_window.messages.deepseek_error", error=str(e))

    def open_deepseek_with_context(self, prompt, response):
        """Open DeepSeek window with pre-filled prompt and response."""
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
                audio_player=self.audio_player,
                tts_voice=self.tts_voice.get() if self.tts_voice else "pt_BR-faber-medium"
            )
        except Exception as e:
            self._handle_service_error(e)

    def stop_all_audio(self):
        """Stop any currently playing audio."""
        logger.info("Stopping all audio")
        self.audio_player.stop()

    def get_gpu_memory_usage(self):
        """
        Return GPU memory usage as a string (e.g., "VRAM: 2.3/8.0 GB").
        Uses rocm-smi for AMD GPUs, nvidia-smi for NVIDIA, and falls back to torch.
        """
        try:
            import subprocess
            import shutil
            
            # Try rocm-smi (AMD)
            if shutil.which('rocm-smi') is not None:
                logger.debug("Trying rocm-smi")
                try:
                    result = subprocess.run(['rocm-smi', '--showmeminfo', 'vram'],
                                            capture_output=True, text=True, timeout=2, check=False)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        total = used = None
                        for line in lines:
                            if 'VRAM Total' in line:
                                parts = line.split(':')
                                if len(parts) > 1:
                                    value_str = parts[1].strip()
                                    import re
                                    num_match = re.search(r'(\d+\.?\d*)', value_str)
                                    if num_match:
                                        total = float(num_match.group(1))
                                        if 'GB' in value_str:
                                            total_gb = total
                                        else:
                                            total_gb = total / 1024
                            elif 'VRAM Used' in line:
                                parts = line.split(':')
                                if len(parts) > 1:
                                    value_str = parts[1].strip()
                                    num_match = re.search(r'(\d+\.?\d*)', value_str)
                                    if num_match:
                                        used = float(num_match.group(1))
                                        if 'GB' in value_str:
                                            used_gb = used
                                        else:
                                            used_gb = used / 1024
                        if total is not None and used is not None:
                            result_str = f"VRAM: {used_gb:.1f}/{total_gb:.1f} GB"
                            logger.debug(f"rocm-smi result: {result_str}")
                            return result_str
                except Exception as e:
                    logger.debug(f"rocm-smi failed: {e}")
            
            # Fallback to nvidia-smi (NVIDIA)
            if shutil.which('nvidia-smi') is not None:
                logger.debug("Trying nvidia-smi")
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total',
                                            '--format=csv,noheader,nounits'],
                                            capture_output=True, text=True, timeout=2, check=False)
                    if result.returncode == 0:
                        used_str, total_str = result.stdout.strip().split(',')
                        used_gb = round(float(used_str) / 1024, 1)
                        total_gb = round(float(total_str) / 1024, 1)
                        result_str = f"VRAM: {used_gb}/{total_gb} GB"
                        logger.debug(f"nvidia-smi result: {result_str}")
                        return result_str
                except Exception as e:
                    logger.debug(f"nvidia-smi failed: {e}")
            
            # Fallback using torch (only total and allocated)
            if torch.cuda.is_available():
                logger.debug("Trying torch.cuda")
                try:
                    device = torch.cuda.current_device()
                    total_memory = torch.cuda.get_device_properties(device).total_memory
                    total_gb = round(total_memory / (1024**3), 1)
                    
                    allocated = torch.cuda.memory_allocated(device)
                    allocated_gb = round(allocated / (1024**3), 1)
                    
                    if allocated_gb > 0:
                        result_str = f"VRAM: {allocated_gb:.1f}/{total_gb:.1f} GB (PyTorch)"
                    else:
                        result_str = f"VRAM: ?/{total_gb:.1f} GB"
                    
                    logger.debug(f"torch result: {result_str}")
                    return result_str
                except Exception as e:
                    logger.debug(f"torch.cuda query failed: {e}")
            
        except Exception as e:
            logger.debug(f"GPU memory query failed: {e}")
        
        return "VRAM: N/A"
    
    def show_notification(self, title, message):
        """Send a desktop notification using notify-send."""
        try:
            import subprocess
            subprocess.run(['notify-send', title, message])
            logger.debug(f"Notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def show_error(self, title, message):
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self.root)

    def show_info(self, title, message):
        from tkinter import messagebox
        messagebox.showinfo(title, message, parent=self.root)

    def show_warning(self, title, message):
        from tkinter import messagebox
        messagebox.showwarning(title, message, parent=self.root)

    def clear_translation_cache(self):
        """Clear the translation cache."""
        self.translation_service.clear_cache()
        self.show_info(_("dialogs.common.info"), _("translation.cache_cleared"))

    def get_translation_cache_stats(self):
        """Return translation cache statistics."""
        return self.translation_service.cache_stats()

    def quit_app(self):
        """Shutdown the application, save config, and exit."""
        logger.info("Shutting down application")
        config_dict = {
            "model_size": self.model_size.get() if self.model_size else self._model_size,
            "device": self.device.get() if self.device else self._device,
            "source_language": self.current_language.get() if self.current_language else self._current_language,
            "target_language": self.translate_target.get() if self.translate_target else self._translate_target,
            "ui_language": self.ui_language.get() if self.ui_language else self._ui_language,
            "tts_voice": self.tts_voice.get() if self.tts_voice else self._tts_voice,
            "translation_model": self.translation_model.get() if self.translation_model else self._translation_model,
            "idle_timeout": int(self.idle_timeout.get()) if self.idle_timeout else self._idle_timeout
        }
        save_config(config_dict)
        self.stop_all_audio()
        self.model_manager.unload_all()
        if self.root:
            self.root.quit()
        logger.info("Application terminated")
        sys.exit(0)