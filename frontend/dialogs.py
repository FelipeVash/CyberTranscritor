# frontend/dialogs.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from backend.corrector import correct_text

def show_correction_dialog(parent, title, original_text, callback, lang):
    """Exibe diálogo de correção gramatical com confirmação."""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("700x500")
    dialog.transient(parent)
    dialog.grab_set()

    orig_frame = ttk.LabelFrame(dialog, text="Texto Original", padding=5)
    orig_frame.pack(fill="both", expand=True, padx=10, pady=5)
    orig_text = scrolledtext.ScrolledText(orig_frame, wrap=tk.WORD, height=6, font=("Consolas", 10))
    orig_text.pack(fill="both", expand=True)
    orig_text.insert(tk.END, original_text)
    orig_text.config(state=tk.DISABLED)

    # Inicia correção em thread para não travar
    def do_correction():
        corrected = correct_text(original_text, lang)
        dialog.after(0, lambda: display_corrected(corrected))

    def display_corrected(corrected):
        corr_frame = ttk.LabelFrame(dialog, text="Texto Corrigido", padding=5)
        corr_frame.pack(fill="both", expand=True, padx=10, pady=5)
        corr_text = scrolledtext.ScrolledText(corr_frame, wrap=tk.WORD, height=6, font=("Consolas", 10))
        corr_text.pack(fill="both", expand=True)
        corr_text.insert(tk.END, corrected)
        corr_text.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Aplicar",
                   command=lambda: [callback(corrected), dialog.destroy()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    import threading
    threading.Thread(target=do_correction, daemon=True).start()