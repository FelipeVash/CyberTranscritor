# frontend/widgets.py
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
import ttkbootstrap as tb
from utils.helpers import (
    apply_tag, insert_bullet, insert_numbered_list, insert_datetime,
    align_text, insert_table, export_html, import_html, increase_indent, decrease_indent
)
from utils.tooltip import ToolTip

class FormatToolbar(ttk.Frame):
    """Barra de ferramentas de formatação reutilizável com duas linhas."""
    def __init__(self, parent, text_widget, app, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.app = app

        self._create_widgets()

    def _create_widgets(self):
        # Primeira linha
        row1 = ttk.Frame(self)
        row1.pack(fill="x", pady=(0,2))

        # Segunda linha
        row2 = ttk.Frame(self)
        row2.pack(fill="x")

        # ========== LINHA 1 ==========
        # Negrito
        btn_bold = ttk.Button(row1, text="B", width=3, style="Cyan.TButton",
                              command=lambda: apply_tag(self.text_widget, "bold"))
        btn_bold.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_bold, "Negrito (Ctrl+B)")

        # Itálico
        btn_italic = ttk.Button(row1, text="I", width=3, style="Cyan.TButton",
                                command=lambda: apply_tag(self.text_widget, "italic"))
        btn_italic.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_italic, "Itálico (Ctrl+I)")

        # Sublinhado
        btn_underline = ttk.Button(row1, text="U", width=3, style="Cyan.TButton",
                                   command=lambda: apply_tag(self.text_widget, "underline"))
        btn_underline.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_underline, "Sublinhado (Ctrl+U)")

        # Tachado
        btn_strike = ttk.Button(row1, text="S", width=3, style="Cyan.TButton",
                                command=lambda: apply_tag(self.text_widget, "overstrike"))
        btn_strike.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_strike, "Tachado")

        # Espaço
        ttk.Label(row1, text=" ").pack(side=tk.LEFT)

        # Tamanho da fonte
        font_sizes = [10, 12, 14, 16, 18, 20, 24]
        font_menu = tb.Menubutton(row1, text="Tamanho ▼", bootstyle="secondary")
        font_menu.pack(side=tk.LEFT, padx=5)
        menu_font = tk.Menu(font_menu, tearoff=0)
        for size in font_sizes:
            menu_font.add_command(label=f"{size} px",
                                  command=lambda s=size: self.text_widget.configure(font=("Consolas", s)))
        font_menu.config(menu=menu_font)
        ToolTip(font_menu, "Alterar tamanho da fonte (todo o texto)")

        # Seletor de cor
        def choose_color():
            color = colorchooser.askcolor(title="Escolha uma cor")[1]
            if color:
                apply_tag(self.text_widget, color)
                self.text_widget.tag_configure(color, foreground=color)
        btn_color = ttk.Button(row1, text="🎨", width=3, style="Cyan.TButton", command=choose_color)
        btn_color.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_color, "Aplicar cor ao texto selecionado")

        # Espaço
        ttk.Label(row1, text="  ").pack(side=tk.LEFT)

        # Título
        btn_heading = ttk.Button(row1, text="H", width=3, style="Cyan.TButton",
                                 command=lambda: apply_tag(self.text_widget, "heading"))
        btn_heading.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_heading, "Aplicar estilo de título")

        # Data/hora
        btn_datetime = ttk.Button(row1, text="🕒", width=3, style="Cyan.TButton",
                                  command=lambda: insert_datetime(self.text_widget))
        btn_datetime.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_datetime, "Inserir data e hora atual")

        # ========== LINHA 2 ==========
        # Alinhar esquerda
        btn_left = ttk.Button(row2, text="⬅", width=3, style="Cyan.TButton",
                              command=lambda: align_text(self.text_widget, "left"))
        btn_left.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_left, "Alinhar parágrafo à esquerda")

        # Centralizar
        btn_center = ttk.Button(row2, text="⏺", width=3, style="Cyan.TButton",
                                command=lambda: align_text(self.text_widget, "center"))
        btn_center.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_center, "Centralizar parágrafo")

        # Alinhar direita
        btn_right = ttk.Button(row2, text="➡", width=3, style="Cyan.TButton",
                               command=lambda: align_text(self.text_widget, "right"))
        btn_right.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_right, "Alinhar parágrafo à direita")

        # Justificar
        btn_justify = ttk.Button(row2, text="↔", width=3, style="Cyan.TButton",
                                 command=lambda: align_text(self.text_widget, "justify"))
        btn_justify.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_justify, "Justificar parágrafo")

        # Espaço
        ttk.Label(row2, text="  ").pack(side=tk.LEFT)

        # Aumentar indentação
        btn_indent = ttk.Button(row2, text="⇢", width=3, style="Cyan.TButton",
                                command=lambda: increase_indent(self.text_widget))
        btn_indent.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_indent, "Aumentar indentação (adicionar 4 espaços)")

        # Diminuir indentação
        btn_dedent = ttk.Button(row2, text="⇠", width=3, style="Cyan.TButton",
                                command=lambda: decrease_indent(self.text_widget))
        btn_dedent.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_dedent, "Diminuir indentação (remover 4 espaços)")

        # Espaço
        ttk.Label(row2, text="  ").pack(side=tk.LEFT)

        # Lista numerada
        btn_numbered = ttk.Button(row2, text="1.", width=3, style="Cyan.TButton",
                                  command=lambda: insert_numbered_list(self.text_widget, self.app))
        btn_numbered.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_numbered, "Inserir/continuar lista numerada (Enter incrementa)")

        # Lista com marcadores
        btn_bullet = ttk.Button(row2, text="•", width=3, style="Cyan.TButton",
                                command=lambda: insert_bullet(self.text_widget))
        btn_bullet.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_bullet, "Inserir/remover marcador na linha atual")

        # Espaço
        ttk.Label(row2, text="  ").pack(side=tk.LEFT)

        # Inserir tabela
        btn_table = ttk.Button(row2, text="⧠", width=3, style="Cyan.TButton",
                               command=lambda: insert_table(self.text_widget))
        btn_table.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_table, "Inserir tabela simples 3x2")

        # Espaço
        ttk.Label(row2, text="  ").pack(side=tk.LEFT)

        # Exportar HTML
        btn_export_html = ttk.Button(row2, text="HTML", width=5, style="Cyan.TButton",
                                     command=lambda: export_html(self.text_widget))
        btn_export_html.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_export_html, "Exportar conteúdo como HTML (texto puro)")

        # Importar HTML
        btn_import_html = ttk.Button(row2, text="IMPORT", width=6, style="Cyan.TButton",
                                     command=lambda: import_html(self.text_widget))
        btn_import_html.pack(side=tk.LEFT, padx=1)
        ToolTip(btn_import_html, "Importar de arquivo HTML (extrai texto puro)")