from core.frontend.styles import configure_styles
# apps/deepseek/window.py
"""
DeepSeek chat window standalone.
Adapted from the original deepseek_window to work independently.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
from datetime import datetime
import numpy as np
import traceback

from core.backend.audio.recorder import AudioRecorder
from core.backend.audio.player import AudioPlayer
from core.utils.tooltip import ToolTip
from core.utils.i18n import _
from core.utils.logger import logger
from core import config
from core.frontend.styles import configure_styles

from .controller import DeepSeekController

class DeepSeekWindow:
    """
    Standalone window for interacting with DeepSeek AI.
    Supports audio input, text input, and TTS output.
    """

    def __init__(self, parent=None, initial_prompt=None, initial_response=None):
        logger.info("Initializing DeepSeekWindow standalone")
        self.parent = parent
        self.audio_player = AudioPlayer()
        self.controller = DeepSeekController()

        self.window = None
        self.is_recording = False
        self.recorder = None
        self.last_response = None
        self.chat_history = []

        # Tkinter variables – will be created in setup_ui after window exists
        self.enable_thinking = None
        self.enable_web_search = None
        self.enable_correction = None

        try:
            self.setup_ui()
            self.setup_bindings()
            if initial_prompt:
                if initial_response is not None and isinstance(initial_response, str):
                    self.send_to_deepseek(initial_prompt, initial_response)
                else:
                    self.send_to_deepseek(initial_prompt)
            logger.info("DeepSeekWindow initialization complete")
        except Exception as e:
            logger.error(f"Error configuring DeepSeekWindow: {e}")
            traceback.print_exc()
            messagebox.showerror(
                _("dialogs.common.error"),
                _("deepseek_window.messages.deepseek_error", error=str(e))
            )
    
    def setup_ui(self):
        logger.debug("Building DeepSeekWindow UI")
        if self.parent:
            self.window = tb.Toplevel(self.parent)
        else:
            self.window = tb.Window(themename="darkly")
            self.window.protocol("WM_DELETE_WINDOW", self.destroy)

        # Aplica os estilos customizados
        style = tb.Style.get_instance()
        configure_styles(style)

        self.window.title(_("deepseek_window.title"))
        self.window.geometry("900x1100")
        self.window.focus_force()

        # Tkinter variables
        self.enable_thinking = tk.BooleanVar(self.window, value=False)
        self.enable_web_search = tk.BooleanVar(self.window, value=False)
        self.enable_correction = tk.BooleanVar(self.window, value=True)

        # Control frame (buttons)
        control_frame = tb.Frame(self.window)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.btn_record = tb.Button(
            control_frame,
            text=_("common.buttons.record"),
            style="Pink.TButton",
            width=18,
            command=self.toggle_recording
        )
        self.btn_record.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_record, text_key="deepseek_window.controls.record_tooltip")

        self.btn_stop_audio = tb.Button(
            control_frame,
            text=_("deepseek_window.controls.stop_audio"),
            style="secondary",
            width=18,
            command=self.stop_audio
        )
        self.btn_stop_audio.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_stop_audio, text_key="deepseek_window.controls.stop_audio_tooltip")

        self.btn_tts = tb.Button(
            control_frame,
            text=_("deepseek_window.controls.listen"),
            style="Cyan.TButton",
            width=18,
            command=self.play_last_response
        )
        self.btn_tts.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_tts, text_key="deepseek_window.controls.listen_tooltip")

        self.status_label = tk.Label(
            control_frame,
            text=_("deepseek_window.labels.status_idle"),
            fg="#888888"
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Options frame (sem padding no construtor, usando ipadx/ipady no pack)
        options_frame = tb.LabelFrame(self.window, text=_("deepseek_window.options_frame"))
        options_frame.pack(fill="x", padx=10, pady=5, ipadx=5, ipady=5)

        chk_think = tb.Checkbutton(
            options_frame,
            text=_("deepseek_window.options.thinking"),
            variable=self.enable_thinking,
            bootstyle="info"
        )
        chk_think.pack(side=tk.LEFT, padx=5)
        ToolTip(chk_think, text_key="deepseek_window.options.thinking_tooltip")

        chk_web = tb.Checkbutton(
            options_frame,
            text=_("deepseek_window.options.web_search"),
            variable=self.enable_web_search,
            bootstyle="info"
        )
        chk_web.pack(side=tk.LEFT, padx=5)
        ToolTip(chk_web, text_key="deepseek_window.options.web_search_tooltip")

        chk_correct = tb.Checkbutton(
            options_frame,
            text=_("deepseek_window.options.correction"),
            variable=self.enable_correction,
            bootstyle="info"
        )
        chk_correct.pack(side=tk.LEFT, padx=5)
        ToolTip(chk_correct, text_key="deepseek_window.options.correction_tooltip")

        # History area
        hist_frame = tb.LabelFrame(self.window, text=_("deepseek_window.labels.history"))
        hist_frame.pack(fill="both", expand=True, padx=10, pady=5, ipadx=10, ipady=10)

        self.hist_area = scrolledtext.ScrolledText(
            hist_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            state=tk.DISABLED
        )
        self.hist_area.pack(fill="both", expand=True)

        # Input area
        input_frame = tb.LabelFrame(self.window, text=_("deepseek_window.labels.input"))
        input_frame.pack(fill="x", padx=10, pady=5, ipadx=5, ipady=5)

        self.input_area = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            height=4
        )
        self.input_area.pack(fill="x", padx=5, pady=5)

        btn_frame = tb.Frame(input_frame)
        btn_frame.pack(fill="x", pady=5)

        send_btn = tb.Button(
            btn_frame,
            text=_("deepseek_window.controls.send_text"),
            style="Cyan.TButton",
            command=self.send_text
        )
        send_btn.pack(side=tk.RIGHT, padx=5)

        hint = tk.Label(
            input_frame,
            text=_("deepseek_window.labels.hint"),
            fg="#888888",
            bg="#2b2b2b",
            font=("Segoe UI", 9)
        )
        hint.pack(pady=2)

        logger.debug("UI setup complete")

    def setup_bindings(self):
        """Set up keyboard bindings."""
        self.input_area.bind("<Return>", self.on_enter_press)
        self.input_area.bind("<Shift-Return>", self.on_shift_enter)
        self.window.bind("<Escape>", lambda e: self.destroy())
        self.window.bind("<Control-r>", lambda e: self.toggle_recording())
        self.window.bind("<Control-R>", lambda e: self.toggle_recording())
        logger.debug("Bindings configured")

    def destroy(self):
        """Destroy the window and free resources."""
        logger.info("Destroying DeepSeek window")
        self.stop_audio()
        if self.window:
            self.window.destroy()

    def stop_audio(self):
        """Stop any ongoing audio playback."""
        self.audio_player.stop()
        self.controller.stop_tts()

    def on_enter_press(self, event):
        """Handle Enter key: send text."""
        self.send_text()
        return "break"

    def on_shift_enter(self, event):
        """Handle Shift+Enter: insert newline."""
        self.input_area.insert(tk.INSERT, "\n")
        return "break"

    def toggle_recording(self):
        """Toggle audio recording on/off."""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_and_send()

    def start_recording(self):
        """Start recording audio."""
        self.recorder = AudioRecorder(samplerate=config.SAMPLE_RATE, channels=config.CHANNELS)
        self.is_recording = True
        self.recorder.start()
        self.btn_record.config(text=_("deepseek_window.controls.stop_record"), style="success.TButton")
        self.status_label.config(text=_("deepseek_window.labels.status_recording"), fg="red")
        logger.info("Recording started")

    def stop_and_send(self):
        """Stop recording and send the transcribed text."""
        self.is_recording = False
        audio = self.recorder.stop()
        self.btn_record.config(text=_("common.buttons.record"), style="Pink.TButton")
        self.status_label.config(text=_("deepseek_window.labels.status_transcribing"), fg="orange")

        if audio.size == 0:
            messagebox.showwarning(
                _("dialogs.common.warning"),
                _("deepseek_window.messages.no_audio"),
                parent=self.window
            )
            self.status_label.config(text=_("deepseek_window.labels.status_idle"), fg="#888888")
            return

        def transcribe_task():
            try:
                lang = "pt"  # Could be made configurable later
                text = self.controller.transcribe_audio(
                    audio,
                    language=lang,
                    apply_correction=self.enable_correction.get()
                )
                if text.startswith("[Erro:") or "áudio muito baixo" in text.lower():
                    self.window.after(0, lambda: self.show_error(
                        _("deepseek_window.messages.transcription_error"), text
                    ))
                    self.window.after(0, lambda: self.status_label.config(
                        text=_("deepseek_window.labels.status_idle"),
                        fg="#888888"
                    ))
                    return
                self.window.after(0, lambda: self.send_to_deepseek(text))
            except Exception as e:
                self.window.after(0, lambda: self.show_error(
                    _("deepseek_window.messages.deepseek_error"), str(e)
                ))
                self.window.after(0, lambda: self.status_label.config(
                    text=_("deepseek_window.labels.status_idle"),
                    fg="#888888"
                ))

        threading.Thread(target=transcribe_task, daemon=True).start()

    def send_text(self):
        """Send the text from input area to DeepSeek."""
        text = self.input_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo(
                _("dialogs.common.info"),
                _("deepseek_window.messages.no_text"),
                parent=self.window
            )
            return
        self.input_area.delete(1.0, tk.END)
        if self.enable_correction.get():
            from core.backend.corrector import correct_text
            text = correct_text(text, "pt")
        self.send_to_deepseek(text)

    def send_to_deepseek(self, text, pre_response=None):
        """Send a query to DeepSeek and display the response."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._add_to_history("user", text, timestamp)

        if pre_response:
            self.last_response = pre_response
            self._add_to_history("assistant", pre_response, timestamp)
            self.status_label.config(text=_("deepseek_window.labels.status_preloaded"), fg="green")
            self._auto_play_response(pre_response)
            return

        self.status_label.config(text=_("deepseek_window.labels.status_consulting"), fg="orange")

        def task():
            response = self.controller.ask_deepseek(
                text,
                enable_web_search=self.enable_web_search.get(),
                enable_thinking=self.enable_thinking.get()
            )
            self.last_response = response
            self.window.after(0, lambda: self._add_to_history(
                "assistant",
                response,
                datetime.now().strftime("%H:%M:%S")
            ))
            self.window.after(0, lambda: self.status_label.config(
                text=_("deepseek_window.labels.status_response"),
                fg="green"
            ))
            self.window.after(0, lambda: self._auto_play_response(response))

        threading.Thread(target=task, daemon=True).start()

    def _auto_play_response(self, text):
        """Automatically play response if it doesn't contain code blocks."""
        if '```' in text:
            logger.debug("Response contains code, skipping auto-play")
            return
        logger.debug("Auto-playing response")
        self.play_response(text)

    def play_last_response(self):
        """Play the last assistant response via TTS."""
        if not self.last_response:
            messagebox.showinfo(
                _("dialogs.common.info"),
                _("deepseek_window.messages.no_response"),
                parent=self.window
            )
            return
        self.play_response(self.last_response)

    def play_response(self, text):
        """Synthesize and play text using TTS."""
        success = self.controller.speak(text, self.audio_player)
        if not success:
            messagebox.showerror(
                _("dialogs.common.error"),
                _("deepseek_window.messages.tts_error"),
                parent=self.window
            )

    def show_error(self, title, message):
        """Display an error message box."""
        messagebox.showerror(title, message, parent=self.window)

    def _add_to_history(self, role, content, timestamp):
        """Add a message to the chat history area."""
        self.hist_area.config(state=tk.NORMAL)
        if role == "user":
            prefix = _("deepseek_window.history.user_prefix", timestamp=timestamp)
            self.hist_area.insert(tk.END, prefix + "\n", "user")
            self.hist_area.tag_configure("user", foreground="#00ffbf")
        else:
            prefix = _("deepseek_window.history.assistant_prefix", timestamp=timestamp)
            self.hist_area.insert(tk.END, prefix + "\n", "assistant")
            self.hist_area.tag_configure("assistant", foreground="#ff00ff")
        self.hist_area.insert(tk.END, content + "\n\n")
        self.hist_area.see(tk.END)
        self.hist_area.config(state=tk.DISABLED)
        logger.debug(f"Added {role} message to history")