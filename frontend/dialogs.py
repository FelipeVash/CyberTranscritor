# frontend/dialogs.py
"""
Custom dialog windows for the application.
Currently provides a grammar correction dialog with real-time processing.
All logging is done through the centralized logger.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from backend.services.correction_service import CorrectionService, CorrectionError
from utils.i18n import _
from utils.logger import logger

def show_correction_dialog(parent, title, original_text, callback, lang, correction_service=None):
    """
    Display a grammar correction dialog with confirmation.

    Args:
        parent: Parent window
        title: Dialog window title
        original_text: Text to be corrected
        callback: Function that receives the corrected text (called when Apply is clicked)
        lang: Language code for correction
        correction_service: Instance of CorrectionService (if None, a new one is created)
    """
    logger.debug(f"Opening correction dialog for language '{lang}'")

    if correction_service is None:
        correction_service = CorrectionService()

    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("700x500")
    dialog.transient(parent)
    dialog.grab_set()

    # Original text frame
    orig_frame = ttk.LabelFrame(dialog, text=_("dialogs.correction.original"), padding=5)
    orig_frame.pack(fill="both", expand=True, padx=10, pady=5)

    orig_text = scrolledtext.ScrolledText(orig_frame, wrap=tk.WORD, height=6, font=("Consolas", 10))
    orig_text.pack(fill="both", expand=True)
    orig_text.insert(tk.END, original_text)
    orig_text.config(state=tk.DISABLED)

    # Status label (shows "Correcting..." or error messages)
    status_label = ttk.Label(dialog, text=_("dialogs.correction.correcting"), foreground="orange")
    status_label.pack(pady=5)

    # Corrected text frame (initially empty, will be populated after correction)
    corr_frame = ttk.LabelFrame(dialog, text=_("dialogs.correction.corrected"), padding=5)
    corr_frame.pack(fill="both", expand=True, padx=10, pady=5)

    corr_text = scrolledtext.ScrolledText(corr_frame, wrap=tk.WORD, height=6, font=("Consolas", 10))
    corr_text.pack(fill="both", expand=True)
    corr_text.config(state=tk.DISABLED)

    # Button frame (initially empty, buttons added after correction)
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=10)

    def do_correction():
        """Run correction in a background thread."""
        try:
            logger.debug("Starting correction thread")
            corrected = correction_service.correct(original_text, lang)
            dialog.after(0, lambda: display_corrected(corrected))
        except CorrectionError as e:
            logger.error(f"Correction error: {e}")
            dialog.after(0, lambda: show_error(_(e.key, **e.kwargs) if hasattr(e, 'key') else str(e)))
        except Exception as e:
            logger.error(f"Unexpected correction error: {e}")
            dialog.after(0, lambda: show_error(f"Unexpected error: {e}"))

    def display_corrected(corrected):
        """Display the corrected text and add action buttons."""
        logger.debug("Correction completed, displaying result")
        status_label.destroy()  # remove status label
        corr_text.config(state=tk.NORMAL)
        corr_text.delete(1.0, tk.END)
        corr_text.insert(tk.END, corrected)
        corr_text.config(state=tk.DISABLED)

        # Add Apply and Cancel buttons
        ttk.Button(btn_frame, text=_("dialogs.correction.apply"),
                   command=lambda: [callback(corrected), dialog.destroy()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=_("dialogs.correction.cancel"),
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def show_error(msg):
        """Display an error message and a Close button."""
        logger.error(f"Correction dialog error: {msg}")
        status_label.config(text=msg, foreground="red")
        ttk.Button(btn_frame, text=_("dialogs.correction.close"),
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    # Start correction in a separate thread
    threading.Thread(target=do_correction, daemon=True).start()