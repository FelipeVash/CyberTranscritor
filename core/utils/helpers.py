# utils/helpers.py
"""
Helper functions for text formatting, list handling, datetime insertion,
alignment, indentation, table insertion, and HTML import/export.
All logging is done through the centralized logger.
"""

import tkinter as tk
import re
from datetime import datetime
from tkinter import messagebox, filedialog
from core.utils.logger import logger

# ========== BASIC FORMATTING FUNCTIONS ==========

def apply_tag(widget, tag):
    """Apply or remove a tag to/from the selected text (toggle)."""
    try:
        start = widget.index(tk.SEL_FIRST)
        end = widget.index(tk.SEL_LAST)
        tags = widget.tag_names(start)
        if tag in tags:
            widget.tag_remove(tag, start, end)
        else:
            widget.tag_add(tag, start, end)
    except tk.TclError:
        # No text selected or other error; ignore silently
        pass

def insert_bullet(widget):
    """Insert or remove a bullet point on the current line."""
    try:
        current_line = widget.index(tk.INSERT).split(".")[0]
        start = f"{current_line}.0"
        end = f"{current_line}.end"
        content = widget.get(start, end)
        if content.startswith("• "):
            widget.delete(start, f"{current_line}.2")
        else:
            widget.insert(start, "• ")
    except Exception as e:
        logger.error(f"Error inserting bullet: {e}")

def insert_numbered_list(widget, app):
    """Insert or continue a numbered list."""
    try:
        current_line = widget.index(tk.INSERT).split(".")[0]
        start = f"{current_line}.0"
        content = widget.get(start, f"{current_line}.end")
        if not content.strip():
            app.last_number += 1
            widget.insert(start, f"{app.last_number}. ")
        else:
            widget.insert(tk.INSERT, "\n")
            app.last_number += 1
            widget.insert(tk.INSERT, f"{app.last_number}. ")
    except Exception as e:
        logger.error(f"Error inserting numbered list: {e}")
        app.last_number += 1
        widget.insert(tk.INSERT, f"{app.last_number}. ")

def insert_datetime(widget):
    """Insert the current date and time in format [dd/mm/yyyy HH:MM:SS]."""
    now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S] ")
    widget.insert(tk.INSERT, now)

def handle_enter(event, widget, app):
    """
    Handle Enter key press for numbered lists and sublevels.
    If the current line starts with a numbered list pattern (e.g., "1. "),
    insert a new line with the next number.
    """
    current_line = widget.index(tk.INSERT).split(".")[0]
    start = f"{current_line}.0"
    content = widget.get(start, f"{current_line}.end")

    # Detect numbered list (e.g., "1. ", "2.3. ", etc.)
    match = re.match(r"^(\d+(\.\d+)*)\.\s", content)
    if match:
        number = match.group(1)
        # Try to increment the last level
        parts = number.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        new_number = '.'.join(parts)
        widget.insert(tk.INSERT, f"\n{new_number}. ")
        return "break"
    else:
        return None

# ========== ALIGNMENT ==========

def align_text(widget, alignment):
    """Apply alignment to the current paragraph (left, center, right, justify)."""
    try:
        current_line = widget.index(tk.INSERT).split(".")[0]
        start = f"{current_line}.0"
        end = f"{current_line}.end"

        # Remove existing alignment tags on this line
        for tag in ["left", "center", "right", "justify"]:
            widget.tag_remove(tag, start, end)

        # Apply the new tag
        widget.tag_add(alignment, start, end)

        # Configure the tag if necessary
        if alignment == "left":
            widget.tag_configure("left", lmargin1=0, lmargin2=0)
        elif alignment == "center":
            widget.tag_configure("center", justify="center")
        elif alignment == "right":
            widget.tag_configure("right", justify="right")
        elif alignment == "justify":
            widget.tag_configure("justify", justify="justify")
    except Exception as e:
        logger.error(f"Error aligning text: {e}")

# ========== INDENTATION ==========

def increase_indent(widget):
    """Increase indentation of the current line (add 4 spaces)."""
    try:
        current_line = widget.index(tk.INSERT).split(".")[0]
        start = f"{current_line}.0"
        widget.insert(start, "    ")
    except Exception as e:
        logger.error(f"Error increasing indent: {e}")

def decrease_indent(widget):
    """Decrease indentation of the current line (remove up to 4 leading spaces)."""
    try:
        current_line = widget.index(tk.INSERT).split(".")[0]
        start = f"{current_line}.0"
        content = widget.get(start, f"{current_line}.4")
        # Remove up to 4 spaces
        num_spaces = len(content) - len(content.lstrip(' '))
        if num_spaces > 0:
            widget.delete(start, f"{current_line}.{num_spaces}")
    except Exception as e:
        logger.error(f"Error decreasing indent: {e}")

# ========== TABLES ==========

def insert_table(widget):
    """Insert a simple 3-column, 2-row table with English headers."""
    try:
        widget.insert(tk.INSERT, "\n+------------+------------+------------+\n")
        widget.insert(tk.INSERT, "| Column 1   | Column 2   | Column 3   |\n")
        widget.insert(tk.INSERT, "+------------+------------+------------+\n")
        widget.insert(tk.INSERT, "|           |           |           |\n")
        widget.insert(tk.INSERT, "+------------+------------+------------+\n")
    except Exception as e:
        logger.error(f"Error inserting table: {e}")

# ========== HTML IMPORT/EXPORT ==========

def export_html(widget):
    """Export the widget content as HTML, preserving tags (as plain text)."""
    from html import escape
    content = widget.get(1.0, tk.END).strip()

    file_path = filedialog.asksaveasfilename(defaultextension=".html",
                                             filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"<html><body><pre>{escape(content)}</pre></body></html>")
            messagebox.showinfo("Export", f"Content exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting HTML: {e}")
            messagebox.showerror("Error", f"Failed to export: {e}")

def import_html(widget):
    """Import content from an HTML file and insert into widget (plain text only)."""
    file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            import re
            clean_text = re.sub(r'<[^>]+>', '', content)
            widget.insert(tk.END, clean_text)
            messagebox.showinfo("Import", "Content imported (tags removed).")
        except Exception as e:
            logger.error(f"Error importing HTML: {e}")
            messagebox.showerror("Error", f"Failed to import: {e}")