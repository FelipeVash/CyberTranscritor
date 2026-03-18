"""
Dialog windows for the application.
Contains correction dialog and close confirmation dialog.
All logging is done through the centralized logger.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from core.utils.i18n import _
from core.utils.logger import logger
from core.backend.services.correction_service import CorrectionService

# ==================== CORRECTION DIALOG ====================

def show_correction_dialog(parent, title, initial_text, callback, language, correction_service=None):
    """
    Display a dialog for text correction using LanguageTool.
    
    Args:
        parent: Parent window
        title: Dialog title
        initial_text: Text to correct
        callback: Function to call with corrected text
        language: Language code (e.g., 'pt', 'en')
        correction_service: Optional CorrectionService instance
    """
    dialog = tb.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("700x500")
    dialog.transient(parent)
    dialog.grab_set()

    # Centralizar
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
    y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")

    # Área de texto
    text_frame = ttk.Frame(dialog, padding=10)
    text_frame.pack(fill=tk.BOTH, expand=True)

    text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 11),
                          bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
    text_widget.insert(tk.END, initial_text)
    text_widget.pack(fill=tk.BOTH, expand=True)

    # Barra de rolagem
    scrollbar = ttk.Scrollbar(text_widget, orient=tk.VERTICAL, command=text_widget.yview)
    text_widget.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Frame de botões
    btn_frame = ttk.Frame(dialog, padding=10)
    btn_frame.pack(fill=tk.X)

    def apply_correction():
        """Apply grammar correction to the text."""
        if correction_service:
            try:
                corrected = correction_service.correct(text_widget.get(1.0, tk.END).strip(), language)
                text_widget.delete(1.0, tk.END)
                text_widget.insert(tk.END, corrected)
                logger.debug("Correction applied")
            except Exception as e:
                logger.error(f"Correction failed: {e}")
                messagebox.showerror(_("dialogs.common.error"), str(e), parent=dialog)

    def ok():
        """Confirm and return the corrected text."""
        callback(text_widget.get(1.0, tk.END).strip())
        dialog.destroy()

    def cancel():
        """Cancel without saving."""
        dialog.destroy()

    # Botões
    if correction_service:
        btn_correct = tb.Button(btn_frame, text=_("dialogs.correction.correct"),
                                style="Cyan.TButton", command=apply_correction)
        btn_correct.pack(side=tk.LEFT, padx=5)

    btn_ok = tb.Button(btn_frame, text=_("common.buttons.ok"),
                       style="Pink.TButton", command=ok)
    btn_ok.pack(side=tk.LEFT, padx=5)

    btn_cancel = tb.Button(btn_frame, text=_("common.buttons.cancel"),
                           style="secondary.TButton", command=cancel)
    btn_cancel.pack(side=tk.LEFT, padx=5)

    dialog.bind("<Escape>", lambda e: cancel())
    dialog.protocol("WM_DELETE_WINDOW", cancel)

# ==================== CLOSE CONFIRMATION DIALOG ====================

def show_close_dialog(parent):
    """
    Exibe um diálogo perguntando se o usuário deseja minimizar para a bandeja ou fechar.
    Retorna 'minimize', 'exit' ou None (se cancelado).
    """
    dialog = tb.Toplevel(parent)
    dialog.title(_("dialogs.close_dialog.title")) 
    dialog.geometry("500x180")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)

    # Centralizar em relação ao pai
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
    y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")

    result = None

    frame = tb.Frame(dialog, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tb.Label(
        frame,
        text=_("dialogs.close_dialog.message"),
        font=("Arial", 12),
        wraplength=350
    ).pack(pady=10)

    btn_frame = tb.Frame(frame)
    btn_frame.pack(pady=10)

    def on_minimize():
        nonlocal result
        result = 'minimize'
        dialog.destroy()

    def on_exit():
        nonlocal result
        result = 'exit'
        dialog.destroy()

    def on_cancel():
        nonlocal result
        result = None
        dialog.destroy()

    tb.Button(
        btn_frame,
        text=_("dialogs.close_dialog.minimize"),
        style="Pink.TButton",
        width=12,
        command=on_minimize
    ).pack(side=tk.LEFT, padx=5)

    tb.Button(
        btn_frame,
        text=_("dialogs.close_dialog.exit"),
        style="Cyan.TButton",
        width=12,
        command=on_exit
    ).pack(side=tk.LEFT, padx=5)

    tb.Button(
        btn_frame,
        text=_("common.buttons.cancel"),
        style="secondary.TButton",
        width=12,
        command=on_cancel
    ).pack(side=tk.LEFT, padx=5)

    dialog.bind("<Escape>", lambda e: on_cancel())
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)

    parent.wait_window(dialog)
    return result