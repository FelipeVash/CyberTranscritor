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
from frontend.settings_window import SettingsWindow
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
        self.root.geometry("1100x1200")  # Updated height

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
        self.vram_var = None
        self.progress_bar = None

        self.setup_menu()
        self.setup_ui()
        self.check_microphone()
        self.setup_bindings()

        # Start system tray icon
        self.tray = TrayIcon(self)
        self.tray.start()

        # Start D-Bus queue polling and GLib event processing
        self.poll_dbus_queue()
        self.process_glib_events()

        # Start VRAM monitoring
        self.update_vram_display()

        self.root.after(1000, self.controller.check_model_idle)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        logger.info("Main window initialized")

    def setup_menu(self):
        """Create the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("main_window.menu.file"), menu=file_menu)
        file_menu.add_command(label=_("main_window.menu.file_menu.save_transcription"), 
                              command=self.controller.save_transcription)
        file_menu.add_command(label=_("main_window.menu.file_menu.save_translations"), 
                              command=self.controller.save_translations)
        file_menu.add_separator()
        file_menu.add_command(label=_("main_window.menu.file_menu.exit"), 
                              command=self.quit_app)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("main_window.menu.edit"), menu=edit_menu)
        edit_menu.add_command(label=_("main_window.menu.edit_menu.correct_transcription"), 
                              command=self.controller.correct_transcription)
        edit_menu.add_command(label=_("main_window.menu.edit_menu.correct_translation"), 
                              command=self.controller.correct_translation)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("main_window.menu.tools"), menu=tools_menu)
        tools_menu.add_command(label=_("main_window.menu.tools_menu.settings"), 
                              command=self.open_settings)
        tools_menu.add_command(label=_("main_window.menu.tools_menu.open_deepseek"), 
                              command=self.controller.open_deepseek_window)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("main_window.menu.help"), menu=help_menu)
        help_menu.add_command(label=_("main_window.menu.help_menu.about"), 
                              command=self.show_about)

        logger.debug("Main menu created")

    def open_settings(self):
        """Open the settings window."""
        SettingsWindow(self.root, self.controller)

    def show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            _("dialogs.about.title"),
            f"{_('dialogs.about.version')}\n\n"
            f"{_('dialogs.about.description')}\n\n"
            f"{_('dialogs.about.license')}",
            parent=self.root
        )

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

        # Row 0: Source language and target language only (model/device moved to settings)
        lbl_source = ttk.Label(control_frame, text=_("main_window.controls.source_language"))
        lbl_source.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        lbl_source.i18n_key = "main_window.controls.source_language"
        lang_combo = tb.Combobox(control_frame, textvariable=self.controller.current_language,
                                   values=list(config.LANGUAGES.keys()),
                                   state="readonly", width=8)
        lang_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ToolTip(lang_combo, text_key="main_window.tooltips.source_language")

        lbl_target = ttk.Label(control_frame, text=_("main_window.controls.target_language"))
        lbl_target.grid(row=0, column=2, padx=20, pady=5, sticky="w")
        lbl_target.i18n_key = "main_window.controls.target_language"
        target_combo = tb.Combobox(control_frame, textvariable=self.controller.translate_target,
                                     values=self.controller.all_languages,
                                     state="readonly", width=8)
        target_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        ToolTip(target_combo, text_key="main_window.tooltips.target_language")

                # Row 1: Action buttons (record, translate, multitranslate, deepseek)
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=15)  # Increased pady for spacing

        # Record button (Pink)
        self.btn_record = ttk.Button(btn_frame, text=_("main_window.controls.buttons.record"),
                                      style="Pink.TButton", width=15, command=self.controller.toggle_recording)
        self.btn_record.pack(side=tk.LEFT, padx=8)  # Increased padx
        self.btn_record.i18n_key = "main_window.controls.buttons.record"
        ToolTip(self.btn_record, text_key="main_window.controls.buttons.record_tooltip")

        # Translate button (Magenta)
        self.btn_translate = ttk.Button(btn_frame, text=_("main_window.controls.buttons.translate"),
                                        style="Magenta.TButton", width=15, command=self.controller.translate_text)
        self.btn_translate.pack(side=tk.LEFT, padx=8)
        self.btn_translate.i18n_key = "main_window.controls.buttons.translate"
        ToolTip(self.btn_translate, text_key="main_window.controls.buttons.translate_tooltip")

        # MultiTranslate button (Magenta)
        self.btn_translate_all = ttk.Button(btn_frame, text=_("main_window.controls.buttons.multitranslate"),
                                            style="Magenta.TButton", width=15, command=self.controller.translate_all)
        self.btn_translate_all.pack(side=tk.LEFT, padx=8)
        self.btn_translate_all.i18n_key = "main_window.controls.buttons.multitranslate"
        ToolTip(self.btn_translate_all, text_key="main_window.controls.buttons.multitranslate_tooltip")

        # DeepSeek button (Cyan)
        self.btn_deepseek = ttk.Button(btn_frame, text=_("main_window.controls.buttons.deepseek"),
                                       style="Cyan.TButton", width=15, command=self.controller.open_deepseek_window)
        self.btn_deepseek.pack(side=tk.LEFT, padx=8)
        self.btn_deepseek.i18n_key = "main_window.controls.buttons.deepseek"
        ToolTip(self.btn_deepseek, text_key="main_window.controls.buttons.deepseek_tooltip")

        # Recording indicator (below buttons)
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
        self.trans_toolbar.pack(fill="x", pady=(0,5))  # já existe
        # Adicionar um espaço extra
        ttk.Label(text_frame, text="").pack(pady=(0,2))  # linha vazia
        self.text_area.pack(fill="both", expand=True, pady=(0,5))

        btn_frame_trans = ttk.Frame(text_frame)
        btn_frame_trans.pack(fill="x", pady=10)
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
        ttk.Label(trans_frame, text="").pack(pady=(0,2))
        self.trans_area.pack(fill="both", expand=True, pady=(0,5))

        btn_frame_resp = ttk.Frame(trans_frame)
        btn_frame_resp.pack(fill="x", pady=10)
        
        # Correct button
        btn_correct_resp = ttk.Button(btn_frame_resp, text=_("main_window.controls.buttons.correct"),
                                       style="Cyan.TButton", command=self.controller.correct_translation)
        btn_correct_resp.pack(side=tk.LEFT, padx=6)
        btn_correct_resp.i18n_key = "main_window.controls.buttons.correct"
        ToolTip(btn_correct_resp, text_key="main_window.controls.buttons.correct_tooltip")

        # Save translations button
        btn_save_translations = ttk.Button(btn_frame_resp, text=_("main_window.controls.buttons.save_translations"),
                                            style="Cyan.TButton", command=self.controller.save_translations)
        btn_save_translations.pack(side=tk.LEFT, padx=6)
        btn_save_translations.i18n_key = "main_window.controls.buttons.save_translations"
        ToolTip(btn_save_translations, text_key="main_window.controls.buttons.save_translations_tooltip")

        # Clear button
        btn_clear_resp = ttk.Button(btn_frame_resp, text=_("main_window.controls.buttons.clear"),
                                     style="secondary", command=lambda: self.trans_area.delete(1.0, tk.END))
        btn_clear_resp.pack(side=tk.LEFT, padx=6)
        btn_clear_resp.i18n_key = "main_window.controls.buttons.clear"
        ToolTip(btn_clear_resp, text_key="main_window.controls.buttons.clear_tooltip")

        # Configure text tags (colors, fonts)
        self._configure_tags()

        # ========== STATUS BAR WITH VRAM INDICATOR ==========
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar()
        self.status_var.set(_("main_window.indicators.ready"))
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        status_label.i18n_key = None
        ToolTip(status_label, text_key="main_window.tooltips.status_bar")

        # VRAM indicator label
        self.vram_var = tk.StringVar()
        self.vram_var.set("VRAM: ...")
        vram_label = ttk.Label(status_frame, textvariable=self.vram_var, relief=tk.SUNKEN, anchor=tk.E, width=18)
        vram_label.pack(side=tk.RIGHT, padx=2)
        ToolTip(vram_label, "GPU memory usage (updated every 5s)")

        # Indeterminate progress bar (packed below status frame)
        self.progress_bar = tb.Progressbar(
            self.root,
            mode='indeterminate',
            bootstyle="info-striped",
            length=200
        )
        self.progress_bar.pack(side=tk.BOTTOM, pady=2)
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

    def update_vram_display(self):
        """Update the VRAM indicator label."""
        usage = self.controller.get_gpu_memory_usage()
        self.vram_var.set(usage)
        self.root.after(5000, self.update_vram_display)  # update every 5 seconds

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
        """Handle window close button: ask whether to exit or minimize to tray."""
        from frontend.dialogs import show_close_dialog
        choice = show_close_dialog(self.root)
        if choice == 'minimize':
            self.hide_window()
        elif choice == 'exit':
            self.quit_app()
        # else: cancel, não faz nada