# frontend/main_window.py
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
import config

class TranscriptionStudio:
    """
    Janela principal do aplicativo.
    Agora apenas constrói a interface e delega ações ao controller.
    """
    def __init__(self, controller):
        self.controller = controller
        self.root = tb.Window(themename="darkly")
        self.root.title(_("main_window.title"))
        self.root.geometry("1100x1000")

        configure_styles(self.root.style)

        self.controller.init_variables(self.root)

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

        self.tray = TrayIcon(self)
        self.tray.start()

        self.poll_dbus_queue()
        self.process_glib_events()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def poll_dbus_queue(self):
        self.controller.process_dbus_queue()
        self.root.after(100, self.poll_dbus_queue)

    def process_glib_events(self):
        try:
            from gi.repository import GLib
            while GLib.main_context_default().iteration(False):
                pass
        except Exception as e:
            print(f"Erro no processamento GLib: {e}")
        self.root.after(10, self.process_glib_events)

    # ==================== INTERFACE ====================
    def setup_ui(self):
        control_frame = ttk.LabelFrame(self.root, text=_("main_window.controls.frame_title"), padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        # Guardar chave para atualização dinâmica
        control_frame.i18n_key = "main_window.controls.frame_title"

        # Linha 0: Modelo, idioma de origem, idioma de destino
        lbl_model = ttk.Label(control_frame, text=_("main_window.controls.model"))
        lbl_model.i18n_key = "main_window.controls.model"
        lbl_model.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        model_combo = tb.Combobox(control_frame, textvariable=self.controller.model_size,
                                   values=["tiny", "base", "small", "medium", "large"],
                                   state="readonly", width=8)
        model_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ToolTip(model_combo, _("main_window.tooltips.model"))
        # Guardar tooltip? Não temos suporte automático, mas a tooltip já usa a chave no momento da criação.

        lbl_source = ttk.Label(control_frame, text=_("main_window.controls.source_language"))
        lbl_source.i18n_key = "main_window.controls.source_language"
        lbl_source.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        lang_combo = tb.Combobox(control_frame, textvariable=self.controller.current_language,
                                   values=list(config.LANGUAGES.keys()),
                                   state="readonly", width=8)
        lang_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ToolTip(lang_combo, _("main_window.tooltips.source_language"))

        lbl_target = ttk.Label(control_frame, text=_("main_window.controls.target_language"))
        lbl_target.i18n_key = "main_window.controls.target_language"
        lbl_target.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        target_combo = tb.Combobox(control_frame, textvariable=self.controller.translate_target,
                                     values=self.controller.all_languages,
                                     state="readonly", width=8)
        target_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ToolTip(target_combo, _("main_window.tooltips.target_language"))

        # Linha 1: Dispositivo e botões principais
        lbl_device = ttk.Label(control_frame, text=_("main_window.controls.device"))
        lbl_device.i18n_key = "main_window.controls.device"
        lbl_device.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        device_combo = tb.Combobox(control_frame, textvariable=self.controller.device,
                                     values=["cpu", "cuda"],
                                     state="readonly", width=8)
        device_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ToolTip(device_combo, _("main_window.tooltips.device"))

        # Linha 4: Seletor de idioma da interface
        lbl_ui_lang = ttk.Label(control_frame, text=_("main_window.controls.ui_language"))
        lbl_ui_lang.i18n_key = "main_window.controls.ui_language"
        lbl_ui_lang.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.lang_combo = tb.Combobox(control_frame, textvariable=self.controller.ui_language,
                                       values=self.controller.get_ui_language_options(),
                                       state="readonly", width=15)
        self.lang_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        ToolTip(self.lang_combo, _("main_window.tooltips.ui_language"))

        # Botão único de gravação (toggle)
        self.btn_record = ttk.Button(control_frame, text=_("main_window.controls.buttons.record"),
                                      style="Pink.TButton", width=20, command=self.controller.toggle_recording)
        self.btn_record.i18n_key = "main_window.controls.buttons.record"
        self.btn_record.grid(row=0, column=2, padx=5, pady=5)
        ToolTip(self.btn_record, _("main_window.controls.buttons.record_tooltip"))

        # Botão Traduzir
        self.btn_translate = ttk.Button(control_frame, text=_("main_window.controls.buttons.translate"),
                                        style="Magenta.TButton", width=20, command=self.controller.translate_text)
        self.btn_translate.i18n_key = "main_window.controls.buttons.translate"
        self.btn_translate.grid(row=1, column=2, padx=5, pady=5)
        ToolTip(self.btn_translate, _("main_window.controls.buttons.translate_tooltip"))

        # Botão MultiTradução
        self.btn_translate_all = ttk.Button(control_frame, text=_("main_window.controls.buttons.multitranslate"),
                                            style="Magenta.TButton", width=20, command=self.controller.translate_all)
        self.btn_translate_all.i18n_key = "main_window.controls.buttons.multitranslate"
        self.btn_translate_all.grid(row=1, column=3, padx=5, pady=5)
        ToolTip(self.btn_translate_all, _("main_window.controls.buttons.multitranslate_tooltip"))

        # Botão Salvar
        self.btn_save = ttk.Button(control_frame, text=_("main_window.controls.buttons.save"),
                                   style="Cyan.TButton", width=20, command=self.controller.save_transcription)
        self.btn_save.i18n_key = "main_window.controls.buttons.save"
        self.btn_save.grid(row=0, column=3, padx=5, pady=5)
        ToolTip(self.btn_save, _("main_window.controls.buttons.save_tooltip"))

        # Botão DeepSeek
        self.btn_deepseek = ttk.Button(control_frame, text=_("main_window.controls.buttons.deepseek"),
                                       style="Cyan.TButton", width=20, command=self.controller.open_deepseek_window)
        self.btn_deepseek.i18n_key = "main_window.controls.buttons.deepseek"
        self.btn_deepseek.grid(row=2, column=2, padx=5, pady=5)
        ToolTip(self.btn_deepseek, _("main_window.controls.buttons.deepseek_tooltip"))

        # Indicador de gravação
        self.rec_indicator = tk.Label(self.root, text=_("main_window.indicators.stopped"),
                                      bg="#404040", fg="#888888",
                                      font=("Arial", 16, "bold"), pady=10)
        self.rec_indicator.i18n_key = "main_window.indicators.stopped"
        self.rec_indicator.pack(fill="x", padx=10, pady=5)
        ToolTip(self.rec_indicator, _("main_window.tooltips.rec_indicator"))

        # ========== ÁREA DE TRANSCRIÇÃO ==========
        text_frame = ttk.LabelFrame(self.root, text=_("main_window.tabs.transcription"), padding=10)
        text_frame.i18n_key = "main_window.tabs.transcription"
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

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
        btn_correct_trans.i18n_key = "main_window.controls.buttons.correct"
        btn_correct_trans.pack(side=tk.LEFT, padx=5)
        ToolTip(btn_correct_trans, _("main_window.controls.buttons.correct_tooltip"))

        btn_clear_trans = ttk.Button(btn_frame_trans, text=_("main_window.controls.buttons.clear"),
                                      style="secondary", command=lambda: self.text_area.delete(1.0, tk.END))
        btn_clear_trans.i18n_key = "main_window.controls.buttons.clear"
        btn_clear_trans.pack(side=tk.LEFT, padx=5)
        ToolTip(btn_clear_trans, _("main_window.controls.buttons.clear_tooltip"))

        # ========== ÁREA DE TRADUÇÕES ==========
        trans_frame = ttk.LabelFrame(self.root, text=_("main_window.tabs.translations"), padding=10)
        trans_frame.i18n_key = "main_window.tabs.translations"
        trans_frame.pack(fill="both", expand=True, padx=10, pady=5)

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
        btn_correct_resp.i18n_key = "main_window.controls.buttons.correct"
        btn_correct_resp.pack(side=tk.LEFT, padx=5)
        ToolTip(btn_correct_resp, _("main_window.controls.buttons.correct_tooltip"))

        btn_clear_resp = ttk.Button(btn_frame_resp, text=_("main_window.controls.buttons.clear"),
                                     style="secondary", command=lambda: self.trans_area.delete(1.0, tk.END))
        btn_clear_resp.i18n_key = "main_window.controls.buttons.clear"
        btn_clear_resp.pack(side=tk.LEFT, padx=5)
        ToolTip(btn_clear_resp, _("main_window.controls.buttons.clear_tooltip"))

        btn_save_trans = ttk.Button(btn_frame_resp, text=_("main_window.controls.buttons.save_translations"),
                                     style="Cyan.TButton", command=self.controller.save_translations)
        btn_save_trans.i18n_key = "main_window.controls.buttons.save_translations"
        btn_save_trans.pack(side=tk.LEFT, padx=5)
        ToolTip(btn_save_trans, _("main_window.controls.buttons.save_translations_tooltip"))

        # Configuração das tags
        self._configure_tags()

        # ========== STATUS BAR E BARRA DE PROGRESSO ==========
        self.status_var = tk.StringVar()
        self.status_var.set(_("main_window.indicators.ready"))

        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)
        ToolTip(status_bar, _("main_window.tooltips.status_bar"))

        self.progress_bar = tb.Progressbar(
            self.root,
            mode='indeterminate',
            bootstyle="info-striped",
            length=200
        )
        self.progress_bar.pack(side=BOTTOM, pady=2)
        self.progress_bar.pack_forget()

        # Passa referências para o controller
        self.controller.set_ui_refs(
            text_area=self.text_area,
            trans_area=self.trans_area,
            btn_record=self.btn_record,
            btn_deepseek=self.btn_deepseek,
            rec_indicator=self.rec_indicator,
            status_var=self.status_var,
            progress_bar=self.progress_bar
        )

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
                messagebox.showerror(
                    _("dialogs.common.error"),
                    _("main_window.status.no_microphone"),
                    parent=self.root
                )
            else:
                self.status_var.set(_("main_window.status.microphone_ok", count=len(input_devices)))
        except Exception as e:
            messagebox.showerror(
                _("dialogs.common.error"),
                _("common.audio.error") + f": {e}",
                parent=self.root
            )

    # ==================== MÉTODOS DELEGADOS AO CONTROLLER (para a bandeja) ====================
    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        if self.controller.deepseek_window and self.controller.deepseek_window.window.winfo_exists():
            self.controller.deepseek_window.show_window()

    def hide_window(self):
        self.root.withdraw()
        self.show_notification(
            _("tray.notifications.app_minimized"),
            _("tray.notifications.app_minimized_msg")
        )

    def quit_app(self):
        self.controller.quit_app()

    def show_notification(self, title, message):
        try:
            import subprocess
            subprocess.run(['notify-send', title, message])
        except Exception as e:
            print(f"Erro ao enviar notificação: {e}")

    def on_closing(self):
        self.hide_window()