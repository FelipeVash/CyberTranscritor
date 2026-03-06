# frontend/dialogs.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from backend.services.correction_service import CorrectionService, CorrectionError
from utils.i18n import _

def show_correction_dialog(parent, title, original_text, callback, lang, correction_service=None):
    """
    Exibe diálogo de correção gramatical com confirmação.
    
    Args:
        parent: janela pai
        title: título do diálogo
        original_text: texto a ser corrigido
        callback: função que recebe o texto corrigido (será chamada ao aplicar)
        lang: código do idioma para correção
        correction_service: instância de CorrectionService (se None, cria uma nova)
    """
    if correction_service is None:
        correction_service = CorrectionService()
    
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("700x500")
    dialog.transient(parent)
    dialog.grab_set()

    # Frame do texto original
    orig_frame = ttk.LabelFrame(dialog, text=_("dialogs.correction.original"), padding=5)
    orig_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    orig_text = scrolledtext.ScrolledText(orig_frame, wrap=tk.WORD, height=6, font=("Consolas", 10))
    orig_text.pack(fill="both", expand=True)
    orig_text.insert(tk.END, original_text)
    orig_text.config(state=tk.DISABLED)

    # Área de status
    status_label = ttk.Label(dialog, text=_("dialogs.correction.correcting"), foreground="orange")
    status_label.pack(pady=5)

    # Frame que conterá o texto corrigido (inicialmente vazio)
    corr_frame = ttk.LabelFrame(dialog, text=_("dialogs.correction.corrected"), padding=5)
    corr_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    corr_text = scrolledtext.ScrolledText(corr_frame, wrap=tk.WORD, height=6, font=("Consolas", 10))
    corr_text.pack(fill="both", expand=True)
    corr_text.config(state=tk.DISABLED)

    # Frame de botões (inicialmente vazio, será preenchido após correção)
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=10)

    def do_correction():
        try:
            corrected = correction_service.correct(original_text, lang)
            dialog.after(0, lambda: display_corrected(corrected))
        except CorrectionError as e:
            dialog.after(0, lambda: show_error(str(e)))
        except Exception as e:
            dialog.after(0, lambda: show_error(f"Erro inesperado: {e}"))

    def display_corrected(corrected):
        status_label.destroy()  # remove status
        corr_text.config(state=tk.NORMAL)
        corr_text.delete(1.0, tk.END)
        corr_text.insert(tk.END, corrected)
        corr_text.config(state=tk.DISABLED)
        
        # Adiciona botões
        ttk.Button(btn_frame, text=_("dialogs.correction.apply"),
                   command=lambda: [callback(corrected), dialog.destroy()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=_("dialogs.correction.cancel"),
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def show_error(msg):
        status_label.config(text=msg, foreground="red")
        ttk.Button(btn_frame, text=_("dialogs.correction.close"),
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def do_correction():
        try:
            corrected = correction_service.correct(original_text, lang)
            dialog.after(0, lambda: display_corrected(corrected))
        except CorrectionError as e:
            dialog.after(0, lambda: show_error(_(e.key, **e.kwargs)))
        except Exception as e:
            dialog.after(0, lambda: show_error(_("errors.correction", error=str(e))))

    # Inicia correção em thread
    threading.Thread(target=do_correction, daemon=True).start()