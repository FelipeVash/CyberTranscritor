# utils/tooltip.py
import tkinter as tk
from utils.i18n import _

class ToolTip:
    _instances = []  # lista de todos os tooltips criados

    def __init__(self, widget, text_key=None, text=None):
        self.widget = widget
        self.text_key = text_key
        self.text = text
        self.tip_window = None
        ToolTip._instances.append(self)
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)
        widget.bind('<ButtonPress>', self.hide_tip)

    @classmethod
    def update_all(cls):
        """Atualiza todos os tooltips com base em suas chaves."""
        for tip in cls._instances:
            if tip.text_key:
                # recalcula na próxima exibição
                pass  # não precisa fazer nada, pois o texto é obtido na hora da exibição

    def update_text(self, new_text_key=None, new_text=None):
        """Atualiza o texto do tooltip (por chave ou string fixa)."""
        if new_text_key is not None:
            self.text_key = new_text_key
            self.text = None
        elif new_text is not None:
            self.text = new_text
            self.text_key = None

    def get_text(self):
        """Retorna o texto atual (traduzido se houver chave)."""
        if self.text_key:
            return _(self.text_key)
        return self.text

    def show_tip(self, event=None):
        if self.tip_window or not self.get_text():
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.get_text(), justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None