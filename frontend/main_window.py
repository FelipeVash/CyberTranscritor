# frontend/main_window.py
"""
Main application window.
Builds the UI and delegates actions to the controller.
All logging is done through the centralized logger.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import tkinter.font as tkfont
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import sys
from pathlib import Path
import traceback

sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.widgets import FormatToolbar
from frontend.styles import configure_styles
from frontend.dialogs import show_correction_dialog
from frontend.tray_icon import TrayIcon
from utils.tooltip import ToolTip
from utils.helpers import handle_enter
from utils.i18n import _
from utils.logger import logger
import config

class TranscriptionStudio:
    """
    Main application window.
    Builds the UI and delegates actions to the controller.
    """

    def __init__(self, controller):
        self.controller = controller
        self.root = tb.Window(themename="darkly")
        self.root.title(_("main_window.title"))
        self.root.geometry("1100x1200")

        configure_styles(self.root.style)

        # Initialize controller variables with the root window
        self.controller.init_variables(self.root)

        # References to UI widgets that need to be accessed
        self.text_area = None
        self.trans_area = None
        self.btn_record = None
        self.btn_deepseek = None
        self.rec_indicator = None
        self.status_var = None
        self.progress_bar = None

        self.setup_ui()
        self.check_microphone()
        self.setup_bindings()

        # Start system tray icon
        self.tray = TrayIcon(self)
        self.tray.start()

        # Start D-Bus queue polling and GLib event processing
        self.poll_dbus_queue()
        self.process_glib_events()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        logger.info("Main window initialized")

    def poll_dbus_queue(self):
        """Periodically call the controller's D-Bus queue processor."""
        self.controller.process_dbus_queue()
        self.root.after(100, self.poll_dbus_queue)

    def process_glib_events(self):
        """Process pending GLib events without blocking the Tkinter main loop."""
        try:
            from gi.repository import GLib
            while GLib.main_context_default().iteration(False):
                pass
        except Exception as e:
            logger.error(f"GLib event processing error: {e}")
        self.root.after(10, self.process_glib_events)

    # ==================== UI CONSTRUCTION ====================

    def setup_ui(self):
        """Create and arrange all UI widgets."""
        logger.debug("Building main window UI")

        control_frame = ttk.LabelFrame(self.root, text=_("main_window.controls.frame_title"), padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        control_frame.i18n_key = "main_window.controls.frame_title"

        # Row 0: Model, source language, target language
        lbl_model = ttk.Label(control_frame, text=_("main_window.controls.model"))
        lbl_model.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        lbl_model.i18n_key = "main_window.controls.model"
        model_combo = tb.Combobox(control_frame, textvariable=self.controller.model_size,
                                   values=["tiny", "base", "small", "medium", "large"],
                                   state="readonly", width=8)
        model_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ToolTip(model_combo, text_key="main_window.tooltips.model")

        lbl_source = ttk.Label(control_frame, text=_("main_window.controls.source_language"))
        lbl_source.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        lbl_source.i18n_key = "main_window.controls.source_language"
        lang_combo = tb.Combobox(control_frame, textvariable=self.controller.current_language,
                                   values=list(config.LANGUAGES.keys()),
                                   state="readonly", width=8)
        lang_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ToolTip(lang_combo, text_key="main_window.tooltips.source_language")

        lbl_target = ttk.Label(control_frame, text=_("main_window.controls.target_language"))
        lbl_target.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        lbl_target.i18n_key = "main_window.controls.target_language"
        target_combo = tb.Combobox(control_frame, textvariable=self.controller.translate_target,
                                     values=self.controller.all_languages,
                                     state="readonly", width=8)
        target_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ToolTip(target_combo, text_key="main_window.tooltips.target_language")

        # Row for UI language selector
        lbl_ui_lang = ttk.Label(control_frame, text=_("main_window.controls.ui_language"))
        lbl_ui_lang.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        lbl_ui_lang.i18n_key = "main_window.controls.ui_language"
        self.lang_combo = tb.Combobox(control_frame, textvariable=self.controller.ui_language,
                                       values=self.controller.get_ui_language_options(),
                                       state="readonly", width=15)
        self.lang_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        ToolTip(self.lang_combo, text_key="main_window.tooltips.ui_language")

        # Row 1: Device and main action buttons
        lbl_device = ttk.Label(control_frame, text=_("main_window.controls.device"))
        lbl_device.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        lbl_device.i18n_key = "main_window.controls.device"
        device_combo = tb.Combobox(control_frame, textvariable=self.controller.device,
                                     values=["cpu", "cuda"],
                                     state="readonly", width=8)
        device_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ToolTip(device_combo, text_key="main_window.tooltips.device")

        # Record button (toggle)
        self.btn_record = ttk.Button(control_frame, text=_("main_window.controls.buttons.record"),
                                      style="Pink.TButton", width=20, command=self.controller.toggle_recording)
        self.btn_record.grid(row=0, column=2, padx=5, pady=5)
        self.btn_record.i18n_key = "main_window.controls.buttons.record"
        ToolTip(self.btn_record, text_key="main_window.controls.buttons.record_tooltip")

        # Translate button
        self.btn_translate = ttk.Button(control_frame, text=_("main_window.controls.buttons.translate"),
                                        style="Magenta.TButton", width=20, command=self.controller.translate_text)
        self.btn_translate.grid(row=1, column=2, padx=5, pady=5)
        self.btn_translate.i18n_key = "main_window.controls.buttons.translate"
        ToolTip(self.btn_translate, text_key="main_window.controls.buttons.translate_tooltip")

        # MultiTranslate button
        self.btn_translate_all = ttk.Button(control_frame, text=_("main_window.controls.buttons.multitranslate"),
                                            style="Magenta.TButton", width=20, command=self.controller.translate_all)
        self.btn_translate_all.grid(row=1, column=3, padx=5, pady=5)
        self.btn_translate_all.i18n_key = "main_window.controls.buttons.multitranslate"
        ToolTip(self.btn_translate_all, text_key="main_window.controls.buttons.multitranslate_tooltip")

        # Save button
        self.btn_save = ttk.Button(control_frame, text=_("main_window.controls.buttons.save"),
                                   style="Cyan.TButton", width=20, command=self.controller.save_transcription)
        self.btn_save.grid(row=0, column=3, padx=5, pady=5)
        self.btn_save.i18n_key = "main_window.controls.buttons.save"
        ToolTip(self.btn_save, text_key="main_window.controls.buttons.save_tooltip")

        # DeepSeek button
        self.btn_deepseek = ttk.Button(control_frame, text=_("main_window.controls.buttons.deepseek"),
                                       style="Cyan.TButton", width=20, command=self.controller.open_deepseek_window)
        self.btn_deepseek.grid(row=2, column=2, padx=5, pady=5)
        self.btn_deepseek.i18n_key = "main_window.controls.buttons.deepseek"
        ToolTip(self.btn_deepseek, text_key="main_window.controls.buttons.deepseek_tooltip")

        # Recording indicator
        self.rec_indicator = tk.Label(self.root, text=_("main_window.indicators.stopped"),
                                      bg="#404040", fg="#888888",
                                      font=("Arial", 16, "bold"), pady=10)
        self.rec_indicator.pack(fill="x", padx=10, pady=5)
        self.rec_indicator.i18n_key = "main_window.indicators.stopped"
        ToolTip(self.rec_indicator, text_key="main_window.tooltips.rec_indicator")

        # ========== TRANSCRIPTION AREA ==========
        text_frame = ttk.LabelFrame(self.root, text=_("main_window.tabs.transcription"), padding=10)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        text_frame.i18n_key = "main_window.tabs.transcription"

        self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=("Consolas", 11),
                                                    bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                                                    height=8)
        self.trans_toolbar = FormatToolbar(text_frame, self.text_area, self)
        self.trans_toolbar.pack(fill="x", pady=(0,5))
        self.text_area.pack(fill="both", expand=True)

        btn_frame_trans = ttk.Frame(text_frame)
        btn_frame_trans.pack(fill="x", pady=5)
        btn_correct_trans = ttk.Button(btn_frame_trans, text=_("main_window.controls.buttons.correct"),
                                        style="Cyan.TButton", command=self.controller.correct_transcription)
        btn_correct_trans.pack(side=tk.LEFT, padx=5)
        btn_correct_trans.i18n_key = "main_window.controls.buttons.correct"
        ToolTip(btn_correct_trans, text_key="main_window.controls.buttons.correct_tooltip")

        btn_clear_trans = ttk.Button(btn_frame_trans, text=_("main_window.controls.buttons.clear"),
                                      style="secondary", command=lambda: self.text_area.delete(1.0, tk.END))
        btn_clear_trans.pack(side=tk.LEFT, padx=5)
        btn_clear_trans.i18n_key = "main_window.controls.buttons.clear"
        ToolTip(btn_clear_trans, text_key="main_window.controls.buttons.clear_tooltip")

        # ========== TRANSLATIONS AREA ==========
        trans_frame = ttk.LabelFrame(self.root, text=_("main_window.tabs.translations"), padding=10)
        trans_frame.pack(fill="both", expand=True, padx=10, pady=5)
        trans_frame.i18n_key = "main_window.tabs.translations"

        self.trans_area = scrolledtext.ScrolledText(trans_frame, wrap=tk.WORD, font=("Consolas", 11),
                                                     bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                                                     height=8)
        self.resp_toolbar = FormatToolbar(trans_frame, self.trans_area, self)
        self.resp_toolbar.pack(fill="x", pady=(0,5))
        self.trans_area.pack(fill="both", expand=True)

        btn_frame_resp = ttk.Frame(trans_frame)
        btn_frame_resp.pack(fill="x", pady=5)
        btn_correct_resp = ttk.Button(btn_frame_resp, text=_("main_window.controls.buttons.correct"),
                                       style="Cyan.TButton", command=self.controller.correct_translation)
        btn_correct_resp.pack(side=tk.LEFT, padx=5)
        btn_correct_resp.i18n_key = "main_window.controls.buttons.correct"
        ToolTip(btn_correct_resp, text_key="main_window.controls.buttons.correct_tooltip")

        btn_clear_resp = ttk.Button(btn_frame_resp, text=_("main_window.controls.buttons.clear"),
                                     style="secondary", command=lambda: self.trans_area.delete(1.0, tk.END))
        btn_clear_resp.pack(side=tk.LEFT, padx=5)
        btn_clear_resp.i18n_key = "main_window.controls.buttons.clear"
        ToolTip(btn_clear_resp, text_key="main_window.controls.buttons.clear_tooltip")

        btn_save_translations = ttk.Button(btn_frame_resp, text=_("main_window.controls.buttons.save_translations"),
                                            style="Cyan.TButton", command=self.controller.save_translations)
        btn_save_translations.pack(side=tk.LEFT, padx=5)
        btn_save_translations.i18n_key = "main_window.controls.buttons.save_translations"
        ToolTip(btn_save_translations, text_key="main_window.controls.buttons.save_translations_tooltip")

        # Configure text tags (colors, fonts)
        self._configure_tags()

        # ========== STATUS BAR AND PROGRESS BAR ==========
        self.status_var = tk.StringVar()
        self.status_var.set(_("main_window.indicators.ready"))

        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)
        status_bar.i18n_key = None  # no fixed text
        ToolTip(status_bar, text_key="main_window.tooltips.status_bar")

        # Indeterminate progress bar
        self.progress_bar = tb.Progressbar(
            self.root,
            mode='indeterminate',
            bootstyle="info-striped",
            length=200
        )
        self.progress_bar.pack(side=BOTTOM, pady=2)
        self.progress_bar.pack_forget()  # initially hidden

        # Pass UI references to the controller
        self.controller.set_ui_refs(
            text_area=self.text_area,
            trans_area=self.trans_area,
            btn_record=self.btn_record,
            btn_deepseek=self.btn_deepseek,
            rec_indicator=self.rec_indicator,
            status_var=self.status_var,
            progress_bar=self.progress_bar
        )

        logger.debug("UI setup completed")

    def _configure_tags(self):
        """Configure text tags for formatting (bold, italic, colors, etc.)."""
        base_font = tkfont.Font(font=self.text_area.cget("font"))
        family = base_font.actual()["family"]
        size = base_font.actual()["size"]
        bold_font = (family, size, "bold")
        italic_font = (family, size, "italic")
        heading_font = (family, size+4, "bold")
        normal_font = (family, size)

        for widget in [self.text_area, self.trans_area]:
            widget.tag_configure("normal", font=normal_font)
            widget.tag_configure("bold", font=bold_font)
            widget.tag_configure("italic", font=italic_font)
            widget.tag_configure("underline", underline=True)
            widget.tag_configure("overstrike", overstrike=True)
            widget.tag_configure("heading", font=heading_font)
            for cor in ["red", "blue", "green", "orange", "purple", "brown"]:
                widget.tag_configure(cor, foreground=cor)

    def setup_bindings(self):
        """Set up keyboard bindings."""
        self.text_area.bind("<Return>", lambda e: handle_enter(e, self.text_area, self))
        self.trans_area.bind("<Return>", lambda e: handle_enter(e, self.trans_area, self))

    def check_microphone(self):
        """Check if a microphone is available and show status."""
        import sounddevice as sd
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d["max_input_channels"] > 0]
            if not input_devices:
                logger.warning("No microphone found")
                messagebox.showerror(
                    _("dialogs.common.error"),
                    _("main_window.status.no_microphone"),
                    parent=self.root
                )
            else:
                self.status_var.set(_("main_window.status.microphone_ok", count=len(input_devices)))
                logger.info(f"Microphone OK: {len(input_devices)} device(s) found")
        except Exception as e:
            logger.error(f"Microphone check failed: {e}")
            messagebox.showerror(
                _("dialogs.common.error"),
                _("common.audio.error") + f": {e}",
                parent=self.root
            )

    # ==================== DELEGATED METHODS (FOR TRAY ICON) ====================

    def show_window(self):
        """Show the main window and bring it to front."""
        logger.debug("Showing main window")
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        if self.controller.deepseek_window and self.controller.deepseek_window.window.winfo_exists():
            self.controller.deepseek_window.show_window()

    def hide_window(self):
        """Hide the main window (minimize to tray)."""
        logger.debug("Hiding main window")
        self.root.withdraw()
        self.show_notification(
            _("tray.notifications.app_minimized"),
            _("tray.notifications.app_minimized_msg")
        )

    def quit_app(self):
        """Quit the application."""
        logger.info("Quit requested from tray")
        self.controller.quit_app()

    def show_notification(self, title, message):
        """Send a desktop notification."""
        try:
            import subprocess
            subprocess.run(['notify-send', title, message])
            logger.debug(f"Notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def on_closing(self):
        """Handle window close button (minimize to tray instead of exiting)."""
        self.hide_window()