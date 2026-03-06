# frontend/settings_window.py
"""
Settings window for the Cyberpunk Transcription Studio.
Allows the user to configure:
- UI language
- Whisper model size
- Device (CPU/GPU)
- TTS voice
- Translation model
- Idle timeout for GPU model unloading
All changes are applied immediately and saved to the configuration file.
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from utils.i18n import _
from utils.logger import logger
from utils.config_persistence import save_config
import re

class SettingsWindow:
    """
    A modal settings window that lets the user change application preferences.
    """

    def __init__(self, parent, controller):
        """
        Initialize the settings window.

        Args:
            parent: The parent window (main window).
            controller: The AppController instance.
        """
        self.controller = controller
        self.parent = parent

        # Create the window
        self.window = tb.Toplevel(parent)
        self.window.title(_("settings_window.title"))
        self.window.geometry("550x500")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.focus_force()

        # Make it modal
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

        # Local variables (copies of current settings)
        self._init_vars()

        # Build UI
        self.setup_ui()

        logger.debug("Settings window opened")

    def _init_vars(self):
        """Initialize local variables with current controller values."""
        # UI language: store the full display string (name + code)
        current_ui_lang = self.controller.ui_language.get()
        self.ui_lang_var = tk.StringVar(value=current_ui_lang)

        # Whisper model size
        self.model_size_var = tk.StringVar(value=self.controller.model_size.get())

        # Device (CPU/GPU)
        self.device_var = tk.StringVar(value=self.controller.device.get())

        # TTS voice: store the code
        self.tts_voice_var = tk.StringVar(value=self.controller.tts_voice.get())

        # Translation model: store the code
        self.trans_model_var = tk.StringVar(value=self.controller.translation_model.get())

        # Idle timeout: store as string (combobox values are strings)
        self.idle_timeout_var = tk.StringVar(value=self.controller.idle_timeout.get())

    def setup_ui(self):
        """Create and arrange the UI widgets."""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== UI Language =====
        lbl_ui_lang = ttk.Label(main_frame, text=_("settings_window.labels.ui_language"))
        lbl_ui_lang.grid(row=0, column=0, sticky=tk.W, pady=5)

        ui_lang_options = self.controller.get_ui_language_options()
        ui_lang_combo = ttk.Combobox(
            main_frame,
            textvariable=self.ui_lang_var,
            values=ui_lang_options,
            state="readonly",
            width=30
        )
        ui_lang_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # ===== Whisper Model =====
        lbl_model = ttk.Label(main_frame, text=_("settings_window.labels.whisper_model"))
        lbl_model.grid(row=1, column=0, sticky=tk.W, pady=5)

        model_options = ["tiny", "base", "small", "medium", "large"]
        model_combo = ttk.Combobox(
            main_frame,
            textvariable=self.model_size_var,
            values=model_options,
            state="readonly",
            width=15
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ToolTip(model_combo, text_key="settings_window.tooltips.whisper_model")

        # ===== Device =====
        lbl_device = ttk.Label(main_frame, text=_("settings_window.labels.device"))
        lbl_device.grid(row=2, column=0, sticky=tk.W, pady=5)

        device_options = ["cpu", "cuda"]
        device_combo = ttk.Combobox(
            main_frame,
            textvariable=self.device_var,
            values=device_options,
            state="readonly",
            width=8
        )
        device_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ToolTip(device_combo, text_key="settings_window.tooltips.device")

        # ===== TTS Voice =====
        lbl_tts_voice = ttk.Label(main_frame, text=_("settings_window.labels.tts_voice"))
        lbl_tts_voice.grid(row=3, column=0, sticky=tk.W, pady=5)

        # Build list of voice names (display) and store codes separately
        voice_codes = list(self.controller.tts_voices.keys())
        voice_names = [self.controller.tts_voices[code] for code in voice_codes]
        tts_voice_combo = ttk.Combobox(
            main_frame,
            values=voice_names,
            state="readonly",
            width=30
        )
        # Set current value by matching code to name
        current_code = self.tts_voice_var.get()
        current_name = self.controller.tts_voices.get(current_code, "")
        if current_name:
            tts_voice_combo.set(current_name)
        else:
            tts_voice_combo.set(voice_names[0] if voice_names else "")
        tts_voice_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # When selection changes, update the variable with the corresponding code
        def on_tts_voice_change(event):
            selected_name = tts_voice_combo.get()
            for code, name in self.controller.tts_voices.items():
                if name == selected_name:
                    self.tts_voice_var.set(code)
                    break
        tts_voice_combo.bind('<<ComboboxSelected>>', on_tts_voice_change)

        # ===== Translation Model =====
        lbl_trans_model = ttk.Label(main_frame, text=_("settings_window.labels.translation_model"))
        lbl_trans_model.grid(row=4, column=0, sticky=tk.W, pady=5)

        model_codes = list(self.controller.translation_models.keys())
        model_names = [self.controller.translation_models[code] for code in model_codes]
        trans_model_combo = ttk.Combobox(
            main_frame,
            values=model_names,
            state="readonly",
            width=30
        )
        current_model_code = self.trans_model_var.get()
        current_model_name = self.controller.translation_models.get(current_model_code, "")
        if current_model_name:
            trans_model_combo.set(current_model_name)
        else:
            trans_model_combo.set(model_names[0] if model_names else "")
        trans_model_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

        def on_trans_model_change(event):
            selected_name = trans_model_combo.get()
            for code, name in self.controller.translation_models.items():
                if name == selected_name:
                    self.trans_model_var.set(code)
                    break
        trans_model_combo.bind('<<ComboboxSelected>>', on_trans_model_change)

        # ===== Idle Timeout =====
        lbl_idle_timeout = ttk.Label(main_frame, text=_("settings_window.labels.idle_timeout"))
        lbl_idle_timeout.grid(row=5, column=0, sticky=tk.W, pady=5)

        timeout_options = ["30", "60", "120", "300", "600"]
        timeout_combo = ttk.Combobox(
            main_frame,
            textvariable=self.idle_timeout_var,
            values=timeout_options,
            state="readonly",
            width=10
        )
        timeout_combo.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

        # ===== Buttons =====
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        btn_ok = ttk.Button(button_frame, text=_("settings_window.buttons.ok"), width=10,
                            command=self.ok)
        btn_ok.pack(side=tk.LEFT, padx=5)

        btn_apply = ttk.Button(button_frame, text=_("settings_window.buttons.apply"), width=10,
                               command=self.apply)
        btn_apply.pack(side=tk.LEFT, padx=5)

        btn_cancel = ttk.Button(button_frame, text=_("settings_window.buttons.cancel"), width=10,
                                command=self.cancel)
        btn_cancel.pack(side=tk.LEFT, padx=5)

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)

    def _apply(self):
        """Apply the selected settings to the controller and save configuration."""
        logger.debug("Applying settings")

        # Update UI language
        selected_ui = self.ui_lang_var.get()
        match = re.search(r'\(([^)]+)\)', selected_ui)
        if match:
            lang_code = match.group(1)
            self.controller.ui_language.set(selected_ui)  # set the display string
            # The trace in controller will handle the actual language change
        else:
            logger.warning(f"Invalid UI language format: {selected_ui}")

        # Update Whisper model size
        self.controller.model_size.set(self.model_size_var.get())

        # Update device
        self.controller.device.set(self.device_var.get())
        # Note: changing device may require reloading models; the controller's trace can handle it.

        # Update TTS voice
        self.controller.tts_voice.set(self.tts_voice_var.get())

        # Update translation model
        self.controller.translation_model.set(self.trans_model_var.get())

        # Update idle timeout
        self.controller.idle_timeout.set(self.idle_timeout_var.get())

        # Save configuration to file
        config_dict = {
            "model_size": self.controller.model_size.get(),
            "device": self.controller.device.get(),
            "source_language": self.controller.current_language.get(),
            "target_language": self.controller.translate_target.get(),
            "ui_language": self.controller.ui_language.get(),
            "tts_voice": self.controller.tts_voice.get(),
            "translation_model": self.controller.translation_model.get(),
            "idle_timeout": int(self.controller.idle_timeout.get())
        }
        save_config(config_dict)
        logger.info("Settings applied and saved")

    def ok(self):
        """Apply settings and close the window."""
        self._apply()
        self.window.destroy()

    def apply(self):
        """Apply settings without closing the window."""
        self._apply()

    def cancel(self):
        """Close the window without applying changes."""
        logger.debug("Settings cancelled")
        self.window.destroy()