"""
DeepSeek chat window with audio recording and TTS capabilities.
All logging is done through the centralized logger.
"""

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

from backend.audio.recorder import AudioRecorder
from backend.deepseek_client import DeepSeekClient
from backend.transcriber import TranscriberGPU
from backend.tts import PiperTTSEngine
from backend.web_search import WebSearch
from backend.corrector import correct_text
import config
from utils.tooltip import ToolTip
from utils.i18n import _
from utils.logger import logger

class DeepSeekWindow:
    """
    A separate window for interacting with DeepSeek AI.
    Supports audio input, text input, and TTS output.
    """

    def __init__(self, parent, main_app, initial_prompt=None, initial_response=None, audio_player=None):
        logger.info("Initializing DeepSeekWindow")
        self.parent = parent
        self.main_app = main_app
        self.audio_player = audio_player

        if main_app is not None and hasattr(main_app, 'device'):
            device = main_app.device.get()
        else:
            device = "cpu"

        # Get current TTS voice from controller
        tts_voice = main_app.tts_voice.get() if main_app and hasattr(main_app, 'tts_voice') else "pt_BR-faber-medium"

        # Initialize TTS engine with the selected voice
        self.tts_engine = None
        try:
            self.tts_engine = PiperTTSEngine(
                voice=tts_voice,  # Pass the voice here
                device="cpu",
                audio_player=self.audio_player
            )
            logger.info(f"TTS Engine (Piper) initialized with voice: {tts_voice}")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            traceback.print_exc()

        # Initialize web search
        self.web_search = None
        try:
            self.web_search = WebSearch()
            logger.info("WebSearch initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSearch: {e}")
            traceback.print_exc()

        self.window = None
        self.is_recording = False
        self.recorder = None
        self.transcriber = main_app.transcriber if main_app is not None else None
        self.deepseek_client = main_app.deepseek_client if main_app is not None else None
        self.last_response = None
        self.chat_history = []

        self.enable_thinking = tk.BooleanVar(value=False)
        self.enable_web_search = tk.BooleanVar(value=False)
        self.enable_correction = tk.BooleanVar(value=True)

        try:
            self.setup_ui()
            self.setup_bindings()
            if initial_prompt:
                self.send_to_deepseek(initial_prompt, initial_response)
            logger.info("DeepSeekWindow initialization complete")
        except Exception as e:
            logger.error(f"Error configuring DeepSeekWindow: {e}")
            traceback.print_exc()
            messagebox.showerror(
                _("dialogs.common.error"),
                _("deepseek_window.messages.deepseek_error", error=str(e)),
                parent=self.window
            )

    def setup_ui(self):
        """Create and arrange all UI widgets."""
        logger.debug("Building DeepSeekWindow UI")
        self.window = tb.Toplevel(self.parent)
        self.window.title(_("deepseek_window.title"))
        self.window.geometry("900x1100")
        self.window.focus_force()

        # Control frame (buttons)
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.btn_record = ttk.Button(
            control_frame,
            text=_("deepseek_window.controls.record"),
            style="Pink.TButton",
            width=20,
            command=self.toggle_recording
        )
        self.btn_record.pack(side=tk.LEFT, padx=2)
        self.btn_record.i18n_key = "deepseek_window.controls.record"
        ToolTip(self.btn_record, text_key="deepseek_window.controls.record_tooltip")

        self.btn_send = ttk.Button(
            control_frame,
            text=_("deepseek_window.controls.send_text"),
            style="Cyan.TButton",
            width=15,
            command=self.send_text
        )
        self.btn_send.pack(side=tk.LEFT, padx=2)
        self.btn_send.i18n_key = "deepseek_window.controls.send_text"
        ToolTip(self.btn_send, text_key="deepseek_window.controls.send_tooltip")

        self.btn_stop_audio = ttk.Button(
            control_frame,
            text=_("deepseek_window.controls.stop_audio"),
            style="secondary",
            width=15,
            command=self.stop_audio
        )
        self.btn_stop_audio.pack(side=tk.LEFT, padx=2)
        self.btn_stop_audio.i18n_key = "deepseek_window.controls.stop_audio"
        ToolTip(self.btn_stop_audio, text_key="deepseek_window.controls.stop_audio_tooltip")

        if self.tts_engine:
            self.btn_tts = ttk.Button(
                control_frame,
                text=_("deepseek_window.controls.listen"),
                style="Cyan.TButton",
                width=15,
                command=self.play_last_response
            )
            self.btn_tts.pack(side=tk.LEFT, padx=2)
            self.btn_tts.i18n_key = "deepseek_window.controls.listen"
            ToolTip(self.btn_tts, text_key="deepseek_window.controls.listen_tooltip")
        else:
            self.btn_tts = ttk.Button(
                control_frame,
                text=_("deepseek_window.controls.tts_unavailable"),
                style="secondary",
                width=15,
                state="disabled"
            )
            self.btn_tts.pack(side=tk.LEFT, padx=2)
            self.btn_tts.i18n_key = "deepseek_window.controls.tts_unavailable"
            ToolTip(self.btn_tts, text_key="deepseek_window.controls.tts_unavailable")

        self.status_label = tk.Label(
            control_frame,
            text=_("deepseek_window.labels.status_idle"),
            fg="#888888"
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)
        self.status_label.i18n_key = "deepseek_window.labels.status_idle"

        # Options frame
        options_frame = ttk.LabelFrame(self.window, text=_("deepseek_window.options_frame"), padding=5)
        options_frame.pack(fill="x", padx=10, pady=5)
        options_frame.i18n_key = "deepseek_window.options_frame"

        chk_think = ttk.Checkbutton(
            options_frame,
            text=_("deepseek_window.options.thinking"),
            variable=self.enable_thinking,
            bootstyle="info"
        )
        chk_think.pack(side=tk.LEFT, padx=5)
        chk_think.i18n_key = "deepseek_window.options.thinking"
        ToolTip(chk_think, text_key="deepseek_window.options.thinking_tooltip")

        chk_web = ttk.Checkbutton(
            options_frame,
            text=_("deepseek_window.options.web_search"),
            variable=self.enable_web_search,
            bootstyle="info"
        )
        chk_web.pack(side=tk.LEFT, padx=5)
        chk_web.i18n_key = "deepseek_window.options.web_search"
        ToolTip(chk_web, text_key="deepseek_window.options.web_search_tooltip")

        chk_correct = ttk.Checkbutton(
            options_frame,
            text=_("deepseek_window.options.correction"),
            variable=self.enable_correction,
            bootstyle="info"
        )
        chk_correct.pack(side=tk.LEFT, padx=5)
        chk_correct.i18n_key = "deepseek_window.options.correction"
        ToolTip(chk_correct, text_key="deepseek_window.options.correction_tooltip")

        # History area
        hist_frame = ttk.LabelFrame(self.window, text=_("deepseek_window.labels.history"), padding=10)
        hist_frame.pack(fill="both", expand=True, padx=10, pady=5)
        hist_frame.i18n_key = "deepseek_window.labels.history"

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
        input_frame = ttk.LabelFrame(self.window, text=_("deepseek_window.labels.input"), padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        input_frame.i18n_key = "deepseek_window.labels.input"

        self.input_area = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            height=4
        )
        self.input_area.pack(fill="x", padx=5, pady=5)

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill="x", pady=5)

        send_btn = ttk.Button(
            btn_frame,
            text=_("deepseek_window.controls.send_text"),
            style="Cyan.TButton",
            command=self.send_text
        )
        send_btn.pack(side=tk.RIGHT, padx=5)
        send_btn.i18n_key = "deepseek_window.controls.send_text"

        hint = tk.Label(
            input_frame,
            text=_("deepseek_window.labels.hint"),
            fg="#888888",
            bg="#2b2b2b",
            font=("Segoe UI", 9)
        )
        hint.pack(pady=2)
        hint.i18n_key = "deepseek_window.labels.hint"

        # Window close protocol
        self.window.protocol("WM_DELETE_WINDOW", self.destroy)
        logger.debug("UI setup complete")

    def setup_bindings(self):
        """Set up keyboard bindings."""
        self.input_area.bind("<Return>", self.on_enter_press)
        self.input_area.bind("<Shift-Return>", self.on_shift_enter)
        self.window.bind("<Escape>", lambda e: self.destroy())
        self.window.bind("<Control-r>", lambda e: self.toggle_recording())
        self.window.bind("<Control-R>", lambda e: self.toggle_recording())
        logger.debug("Bindings configured")

    def hide_window(self):
        """Hide the window (minimize to tray)."""
        logger.debug("Hiding DeepSeek window")
        self.stop_audio()
        self.window.withdraw()

    def show_window(self):
        """Show the window and bring to front."""
        logger.debug("Showing DeepSeek window")
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def destroy(self):
        """Destroy the window and free resources."""
        logger.info("Destroying DeepSeek window")
        self.stop_audio()
        if self.tts_engine:
            self.tts_engine.unload_model()
        if self.window:
            self.window.destroy()

    def stop_audio(self):
        """Stop any ongoing audio playback."""
        if self.tts_engine:
            self.tts_engine.stop()
        if self.main_app and hasattr(self.main_app, 'stop_all_audio'):
            self.main_app.stop_all_audio()

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
        self.btn_record.i18n_key = "deepseek_window.controls.stop_record"
        self.status_label.config(text=_("deepseek_window.labels.status_recording"), fg="red")
        self.status_label.i18n_key = "deepseek_window.labels.status_recording"
        logger.info("Recording started")

    def stop_and_send(self):
        """Stop recording and send the transcribed text."""
        self.is_recording = False
        audio = self.recorder.stop()
        self.btn_record.config(text=_("deepseek_window.controls.record"), style="Pink.TButton")
        self.btn_record.i18n_key = "deepseek_window.controls.record"
        self.status_label.config(text=_("deepseek_window.labels.status_transcribing"), fg="orange")
        self.status_label.i18n_key = "deepseek_window.labels.status_transcribing"

        if audio.size == 0:
            messagebox.showwarning(
                _("dialogs.common.warning"),
                _("deepseek_window.messages.no_audio"),
                parent=self.window
            )
            self.status_label.config(text=_("deepseek_window.labels.status_idle"), fg="#888888")
            self.status_label.i18n_key = "deepseek_window.labels.status_idle"
            return

        if self.transcriber is None:
            try:
                self.transcriber = TranscriberGPU(
                    model_size=self.main_app.model_size.get() if self.main_app else "tiny",
                    device=self.main_app.device.get() if self.main_app else "cuda"
                )
            except Exception as e:
                self.main_app._handle_service_error(e, "deepseek_window.messages.transcription_error")
                self.status_label.config(text=_("deepseek_window.labels.status_idle"), fg="#888888")
                self.status_label.i18n_key = "deepseek_window.labels.status_idle"
                return

        def transcribe_task():
            try:
                lang = self.main_app.current_language.get() if self.main_app else "pt"
                text = self.transcriber.transcribe(audio, language=lang)

                if text.startswith("[Erro:") or text.startswith("❌") or "áudio muito baixo" in text.lower():
                    self.window.after(0, lambda: self.main_app._handle_service_error(
                        Exception(text), "deepseek_window.messages.transcription_error"))
                    self.window.after(0, lambda: self.status_label.config(
                        text=_("deepseek_window.labels.status_idle"),
                        fg="#888888"
                    ))
                    self.window.after(0, lambda: setattr(self.status_label, 'i18n_key', "deepseek_window.labels.status_idle"))
                    return

                if self.enable_correction.get():
                    logger.debug("Applying grammar correction")
                    text = correct_text(text, lang)

                self.window.after(0, lambda: self.send_to_deepseek(text))
            except Exception as e:
                self.window.after(0, lambda: self.main_app._handle_service_error(
                    e, "deepseek_window.messages.deepseek_error", error=str(e)))
                self.window.after(0, lambda: self.status_label.config(
                    text=_("deepseek_window.labels.status_idle"),
                    fg="#888888"
                ))
                self.window.after(0, lambda: setattr(self.status_label, 'i18n_key', "deepseek_window.labels.status_idle"))

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
            lang = self.main_app.current_language.get() if self.main_app else "pt"
            text = correct_text(text, lang)
        self.send_to_deepseek(text)

    def send_to_deepseek(self, text, pre_response=None):
        """Send a query to DeepSeek and display the response."""
        if self.deepseek_client is None:
            try:
                self.deepseek_client = DeepSeekClient()
            except Exception as e:
                self.main_app._handle_service_error(e, "deepseek_window.messages.deepseek_error", error=str(e))
                return

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._add_to_history("user", text, timestamp)

        if pre_response:
            self.last_response = pre_response
            self._add_to_history("assistant", pre_response, timestamp)
            self.status_label.config(text=_("deepseek_window.labels.status_preloaded"), fg="green")
            self.status_label.i18n_key = "deepseek_window.labels.status_preloaded"
            self._auto_play_response(pre_response)
            return

        self.status_label.config(text=_("deepseek_window.labels.status_consulting"), fg="orange")
        self.status_label.i18n_key = "deepseek_window.labels.status_consulting"

        def task():
            try:
                web_results = None
                if self.enable_web_search.get() and self.web_search:
                    logger.info("Performing web search")
                    web_results = asyncio.run(self.web_search.search(text, max_results=3))
                    if web_results:
                        logger.info(f"Found {len(web_results)} search results")

                if web_results:
                    results_text = ""
                    for i, res in enumerate(web_results, 1):
                        results_text += f"\n{i}. {res.get('title', '')}\n   {res.get('snippet', '')}\n   Source: {res.get('url', '')}\n"
                    enhanced_prompt = _("prompts.deepseek_user_with_web", text=text, web_results=results_text)
                else:
                    enhanced_prompt = _("prompts.deepseek_user", text=text)

                if self.enable_thinking.get():
                    enhanced_prompt = _("prompts.thinking_prefix") + "\n\n" + enhanced_prompt

                resposta = self.deepseek_client.ask(
                    enhanced_prompt,
                    system_prompt=_("prompts.deepseek_system"),
                    opt_out=True,
                    enable_thinking=False
                )
                self.last_response = resposta
                self.window.after(0, lambda: self._add_to_history(
                    "assistant",
                    resposta,
                    datetime.now().strftime("%H:%M:%S")
                ))
                self.window.after(0, lambda: self.status_label.config(
                    text=_("deepseek_window.labels.status_response"),
                    fg="green"
                ))
                self.window.after(0, lambda: setattr(self.status_label, 'i18n_key', "deepseek_window.labels.status_response"))
                self.window.after(0, lambda: self._auto_play_response(resposta))
            except Exception as e:
                self.window.after(0, lambda: self.main_app._handle_service_error(
                    e, "deepseek_window.messages.deepseek_error", error=str(e)))
                self.window.after(0, lambda: self.status_label.config(
                    text=_("deepseek_window.labels.status_idle"),
                    fg="#888888"
                ))
                self.window.after(0, lambda: setattr(self.status_label, 'i18n_key', "deepseek_window.labels.status_idle"))

        threading.Thread(target=task, daemon=True).start()

    def _auto_play_response(self, text):
        """Automatically play response if it doesn't contain code blocks."""
        if not self.tts_engine:
            return
        if '```' in text:
            logger.debug("Response contains code, skipping auto-play")
            return
        logger.debug("Auto-playing response")
        self.play_response(text)

    def play_last_response(self):
        """Play the last assistant response via TTS."""
        if not self.tts_engine:
            messagebox.showerror(
                _("dialogs.common.error"),
                _("deepseek_window.messages.tts_error"),
                parent=self.window
            )
            return
        if not self.last_response:
            messagebox.showinfo(
                _("dialogs.common.info"),
                _("deepseek_window.messages.no_response"),
                parent=self.window
            )
            return
        logger.info("Playing last response")
        self.play_response(self.last_response)

    def play_response(self, text):
        """Synthesize and play text using TTS."""
        file_path = self.tts_engine.synthesize(text)
        if file_path:
            self.tts_engine.play_audio(file_path)

    def show_notification(self, title, message):
        """Send a desktop notification."""
        try:
            subprocess.run(['notify-send', title, message])
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

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