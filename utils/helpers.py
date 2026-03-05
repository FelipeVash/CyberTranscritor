# utils/helpers.py
import tkinter as tk
import re
from datetime import datetime
from tkinter import messagebox, filedialog

# ========== FUNÇÕES BÁSICAS DE FORMATAÇÃO ==========
def apply_tag(widget, tag):
    """Aplica ou remove a tag no texto selecionado (toggle)."""
    try:
        start = widget.index(tk.SEL_FIRST)
        end = widget.index(tk.SEL_LAST)
        tags = widget.tag_names(start)
        if tag in tags:
            widget.tag_remove(tag, start, end)
        else:
            widget.tag_add(tag, start, end)
    except tk.TclError:
        pass

def insert_bullet(widget):
    """Insere ou remove bullet point na linha atual."""
    try:
        linha_atual = widget.index(tk.INSERT).split(".")[0]
        start = f"{linha_atual}.0"
        end = f"{linha_atual}.end"
        conteudo = widget.get(start, end)
        if conteudo.startswith("• "):
            widget.delete(start, f"{linha_atual}.2")
        else:
            widget.insert(start, "• ")
    except Exception:
        pass

def insert_numbered_list(widget, app):
    """Insere ou continua lista numerada."""
    try:
        linha_atual = widget.index(tk.INSERT).split(".")[0]
        start = f"{linha_atual}.0"
        conteudo = widget.get(start, f"{linha_atual}.end")
        if not conteudo.strip():
            app.last_number += 1
            widget.insert(start, f"{app.last_number}. ")
        else:
            widget.insert(tk.INSERT, "\n")
            app.last_number += 1
            widget.insert(tk.INSERT, f"{app.last_number}. ")
    except Exception:
        app.last_number += 1
        widget.insert(tk.INSERT, f"{app.last_number}. ")

def insert_datetime(widget):
    """Insere a data e hora atual no formato [dd/mm/aaaa HH:MM:SS]."""
    now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S] ")
    widget.insert(tk.INSERT, now)

def handle_enter(event, widget, app):
    """Gerencia a tecla Enter para listas numeradas e subníveis."""
    linha_atual = widget.index(tk.INSERT).split(".")[0]
    start = f"{linha_atual}.0"
    conteudo = widget.get(start, f"{linha_atual}.end")
    
    # Detectar lista numerada (ex: "1. ", "2.3. ", etc.)
    match = re.match(r"^(\d+(\.\d+)*)\.\s", conteudo)
    if match:
        numero = match.group(1)
        # Tenta incrementar o último nível
        partes = numero.split('.')
        partes[-1] = str(int(partes[-1]) + 1)
        novo_numero = '.'.join(partes)
        widget.insert(tk.INSERT, f"\n{novo_numero}. ")
        return "break"
    else:
        return None

# ========== ALINHAMENTO ==========
def align_text(widget, alignment):
    """Aplica alinhamento ao parágrafo atual (left, center, right, justify)."""
    try:
        # Obtém o índice do início da linha atual
        linha_atual = widget.index(tk.INSERT).split(".")[0]
        start = f"{linha_atual}.0"
        end = f"{linha_atual}.end"
        
        # Remove tags de alinhamento existentes na linha
        for tag in ["left", "center", "right", "justify"]:
            widget.tag_remove(tag, start, end)
        
        # Aplica a nova tag
        widget.tag_add(alignment, start, end)
        
        # Configura a tag se necessário
        if alignment == "left":
            widget.tag_configure("left", lmargin1=0, lmargin2=0)
        elif alignment == "center":
            widget.tag_configure("center", justify="center")
        elif alignment == "right":
            widget.tag_configure("right", justify="right")
        elif alignment == "justify":
            widget.tag_configure("justify", justify="justify")
    except Exception:
        pass

# ========== INDENTAÇÃO ==========
def increase_indent(widget):
    """Aumenta a indentação da linha atual (adiciona 4 espaços)."""
    try:
        linha_atual = widget.index(tk.INSERT).split(".")[0]
        start = f"{linha_atual}.0"
        widget.insert(start, "    ")
    except Exception:
        pass

def decrease_indent(widget):
    """Diminui a indentação da linha atual (remove até 4 espaços do início)."""
    try:
        linha_atual = widget.index(tk.INSERT).split(".")[0]
        start = f"{linha_atual}.0"
        conteudo = widget.get(start, f"{linha_atual}.4")
        # Remove até 4 espaços
        num_spaces = len(conteudo) - len(conteudo.lstrip(' '))
        if num_spaces > 0:
            widget.delete(start, f"{linha_atual}.{num_spaces}")
    except Exception:
        pass

# ========== TABELAS ==========
def insert_table(widget):
    """Insere uma tabela simples com 3 colunas e 2 linhas."""
    try:
        widget.insert(tk.INSERT, "\n+------------+------------+------------+\n")
        widget.insert(tk.INSERT, "| Coluna 1   | Coluna 2   | Coluna 3   |\n")
        widget.insert(tk.INSERT, "+------------+------------+------------+\n")
        widget.insert(tk.INSERT, "|           |           |           |\n")
        widget.insert(tk.INSERT, "+------------+------------+------------+\n")
    except Exception:
        pass

# ========== IMPORTAÇÃO/EXPORTAÇÃO DE RICH TEXT ==========
def export_html(widget):
    """Exporta o conteúdo do widget como HTML, preservando tags."""
    from html import escape
    conteudo = widget.get(1.0, tk.END).strip()
    
    file_path = filedialog.asksaveasfilename(defaultextension=".html",
                                             filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"<html><body><pre>{escape(conteudo)}</pre></body></html>")
        messagebox.showinfo("Exportar", f"Conteúdo exportado para {file_path}")

def import_html(widget):
    """Importa conteúdo de um arquivo HTML e insere no widget (texto puro)."""
    file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
        import re
        texto_limpo = re.sub(r'<[^>]+>', '', conteudo)
        widget.insert(tk.END, texto_limpo)
        messagebox.showinfo("Importar", "Conteúdo importado (tags removidas).")