"""
Meeting recording window (independent application).
Allows user to select audio sink, record, and later process minutes.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from utils.i18n import _
from utils.tooltip import ToolTip
from utils.logger import logger

class MeetingWindow:
    """
    Window for meeting recording and minutes generation.
    Independent of main application.
    """

    def __init__(self, controller):
        self.controller = controller
        self.root = tb.Window(themename="darkly")
        self.root.title("🎤 Gravação de Reuniões")
        self.root.geometry("800x600")

        # Connect controller callbacks
        self.controller.on_status_update = self.update_status

        self.setup_ui()
        self.refresh_sinks()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Create and arrange widgets."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=True)

        # Sink selection
        sink_frame = ttk.LabelFrame(main_frame, text="Dispositivo de Áudio (Sink)", padding=5)
        sink_frame.pack(fill=X, pady=5)

        self.sink_var = tk.StringVar()
        self.sink_combo = ttk.Combobox(sink_frame, textvariable=self.sink_var,
                                        state="readonly", width=50)
        self.sink_combo.pack(side=LEFT, padx=5)

        btn_refresh = ttk.Button(sink_frame, text="↻", width=3, command=self.refresh_sinks)
        btn_refresh.pack(side=LEFT, padx=2)

        # Control buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=10)

        self.btn_record = ttk.Button(btn_frame, text="⏺ Iniciar Gravação",
                                      style="success.TButton", width=20,
                                      command=self.toggle_recording)
        self.btn_record.pack(side=LEFT, padx=5)

        self.btn_process = ttk.Button(btn_frame, text="⚙️ Processar (futuro)",
                                      style="info.TButton", width=20,
                                      command=self.process_recording)
        self.btn_process.pack(side=LEFT, padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(main_frame, textvariable=self.status_var,
                                  relief=SUNKEN, anchor=W)
        status_label.pack(fill=X, pady=5)

        # Log area (for future real-time updates)
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=5)
        log_frame.pack(fill=BOTH, expand=True, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=WORD,
                                                   font=("Consolas", 10),
                                                   bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill=BOTH, expand=True)

    def refresh_sinks(self):
        """Update the sink combobox with current list."""
        sinks = self.controller.get_sinks()
        self.sink_combo['values'] = sinks
        if sinks:
            self.sink_combo.current(0)
        self.log("Sinks atualizados")

    def toggle_recording(self):
        """Start or stop recording."""
        if not self.controller.is_recording:
            sink = self.sink_var.get()
            if not sink:
                self.log("Selecione um sink de áudio", error=True)
                return
            self.controller.start_recording(sink)
            self.btn_record.config(text="⏹ Parar Gravação", style="danger.TButton")
        else:
            self.controller.stop_recording()
            self.btn_record.config(text="⏺ Iniciar Gravação", style="success.TButton")

    def process_recording(self):
        """Placeholder for future processing pipeline."""
        self.log("Processamento não implementado ainda.")

    def update_status(self, message):
        """Update status bar from controller."""
        self.status_var.set(message)

    def log(self, message, error=False):
        """Add message to log area."""
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def on_closing(self):
        """Clean up and close."""
        if self.controller.is_recording:
            self.controller.stop_recording()
        self.controller.cleanup()
        self.root.destroy()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()