# apps/meeting/window.py
"""
Meeting window for recording and processing meetings.
Independent from main application.
All logging is done through the centralized logger.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from core.utils.i18n import _
from core.utils.logger import logger
from apps.meeting.controller import MeetingController
from core.frontend.styles import configure_styles

class MeetingWindow:
    """
    Standalone window for meeting recording and processing.
    """

    def __init__(self):
        # Usa tb.Window em vez de tk.Tk para aplicar o tema
        self.root = tb.Window(themename="darkly")
        self.root.title("🎤 Meeting Recorder")
        self.root.geometry("700x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Aplica os estilos customizados
        style = tb.Style.get_instance()
        configure_styles(style)

        self.controller = MeetingController(self)

        self.selected_sink = tk.StringVar()
        self.status_var = tk.StringVar(value="Pronto")
        self.speaker_var = tk.StringVar(value="Ninguém falando")

        self.setup_ui()
        self.refresh_sinks()

        logger.info("Meeting window initialized")

    def setup_ui(self):
        """Create UI elements."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sink selection
        sink_frame = ttk.LabelFrame(main_frame, text="Fonte de Áudio")
        sink_frame.pack(fill=tk.X, pady=5)

        sink_combo = ttk.Combobox(sink_frame, textvariable=self.selected_sink, state="readonly")
        sink_combo.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.sink_combo = sink_combo

        refresh_btn = ttk.Button(sink_frame, text="↻", width=3, command=self.refresh_sinks)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        self.start_btn = tb.Button(
            control_frame,
            text=_("common.buttons.record"),
            style="Pink.TButton",
            width=20,
            command=self.start_recording
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tb.Button(
            control_frame,
            text=_("common.buttons.stop_record"),
            style="secondary.TButton",
            width=20,
            state=tk.DISABLED,
            command=self.stop_recording
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Current speaker label
        speaker_frame = ttk.LabelFrame(main_frame, text="Falante Atual")
        speaker_frame.pack(fill=tk.X, pady=5)
        speaker_label = ttk.Label(speaker_frame, textvariable=self.speaker_var,
                                   font=("Arial", 14), foreground="blue")
        speaker_label.pack(pady=10)

        # Status bar
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Transcript area (placeholder for later)
        transcript_frame = ttk.LabelFrame(main_frame, text="Transcrição")
        transcript_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.transcript_text = tk.Text(transcript_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.transcript_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def refresh_sinks(self):
        """Refresh list of audio sinks."""
        sinks = self.controller.list_sinks()
        self.sink_combo['values'] = sinks
        if sinks:
            self.selected_sink.set(sinks[0])

    def start_recording(self):
        """Start recording."""
        sink = self.selected_sink.get()
        if not sink:
            messagebox.showerror("Erro", "Selecione uma fonte de áudio.")
            return
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Gravando...")
        self.speaker_var.set("Aguardando...")
        self.controller.start_recording(sink)

    def stop_recording(self):
        """Stop recording and start processing."""
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Parando...")
        self.controller.stop_recording()

    def update_current_speaker(self, speaker):
        """Update UI with current speaker (called from controller thread)."""
        self.speaker_var.set(f"Falante: {speaker}")

    def show_processing(self, processing):
        """Show/hide processing indicator."""
        if processing:
            self.status_var.set("Processando áudio...")
        else:
            self.status_var.set("Pronto")

    def display_transcript(self, text):
        """Display transcript (placeholder for now)."""
        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete(1.0, tk.END)
        self.transcript_text.insert(tk.END, text)
        self.transcript_text.config(state=tk.DISABLED)

    def show_error(self, title, message):
        """Display error message box."""
        messagebox.showerror(title, message, parent=self.root)

    def on_close(self):
        """Handle window close."""
        self.controller.stop_recording()
        self.root.destroy()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()