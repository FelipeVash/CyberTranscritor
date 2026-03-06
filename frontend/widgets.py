# frontend/widgets.py
"""
Custom reusable widgets for the application.
Provides a formatting toolbar with buttons for text styling.
All logging is done through the centralized logger.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
import ttkbootstrap as tb
from utils.helpers import (
    apply_tag, insert_bullet, insert_numbered_list, insert_datetime,
    align_text, insert_table, export_html, import_html, increase_indent, decrease_indent
)
from utils.tooltip import ToolTip
from utils.i18n import _
from utils.logger import logger

class FormatToolbar(ttk.Frame):
    """
    Reusable formatting toolbar with two rows of buttons.
    Provides text styling (bold, italic, underline, etc.), alignment,
    lists, tables, and HTML import/export.
    """

    def __init__(self, parent, text_widget, app, *args, **kwargs):
        """
        Initialize the toolbar.

        Args:
            parent: Parent widget
            text_widget: The scrolled text widget to apply formatting to
            app: Reference to the main application (for list numbering)
        """
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.app = app
        self._create_widgets()
        logger.debug("FormatToolbar created")

    def _create_widgets(self):
        """Create and arrange all toolbar buttons."""
        # First row
        row1 = ttk.Frame(self)
        row1.pack(fill="x", pady=(0,2))
        # Second row
        row2 = ttk.Frame(self)
        row2.pack(fill="x")

        # ========== ROW 1 ==========
        # Bold
        btn_bold = ttk.Button(row1, text=_("main_window.format_toolbar.bold"), width=3, style="Cyan.TButton",
                              command=lambda: apply_tag(self.text_widget, "bold"))
        btn_bold.pack(side=tk.LEFT, padx=1)
        btn_bold.i18n_key = "main_window.format_toolbar.bold"
        ToolTip(btn_bold, text_key="main_window.format_toolbar.bold_tooltip")

        # Italic
        btn_italic = ttk.Button(row1, text=_("main_window.format_toolbar.italic"), width=3, style="Cyan.TButton",
                                command=lambda: apply_tag(self.text_widget, "italic"))
        btn_italic.pack(side=tk.LEFT, padx=1)
        btn_italic.i18n_key = "main_window.format_toolbar.italic"
        ToolTip(btn_italic, text_key="main_window.format_toolbar.italic_tooltip")

        # Underline
        btn_underline = ttk.Button(row1, text=_("main_window.format_toolbar.underline"), width=3, style="Cyan.TButton",
                                   command=lambda: apply_tag(self.text_widget, "underline"))
        btn_underline.pack(side=tk.LEFT, padx=1)
        btn_underline.i18n_key = "main_window.format_toolbar.underline"
        ToolTip(btn_underline, text_key="main_window.format_toolbar.underline_tooltip")

        # Strikethrough
        btn_strike = ttk.Button(row1, text=_("main_window.format_toolbar.strike"), width=3, style="Cyan.TButton",
                                command=lambda: apply_tag(self.text_widget, "overstrike"))
        btn_strike.pack(side=tk.LEFT, padx=1)
        btn_strike.i18n_key = "main_window.format_toolbar.strike"
        ToolTip(btn_strike, text_key="main_window.format_toolbar.strike_tooltip")

        # Spacer
        ttk.Label(row1, text=" ").pack(side=tk.LEFT)

        # Font size menu
        font_sizes = [10, 12, 14, 16, 18, 20, 24]
        font_menu = tb.Menubutton(row1, text=_("main_window.format_toolbar.font_size"), bootstyle="secondary")
        font_menu.pack(side=tk.LEFT, padx=5)
        font_menu.i18n_key = "main_window.format_toolbar.font_size"
        menu_font = tk.Menu(font_menu, tearoff=0)
        for size in font_sizes:
            menu_font.add_command(label=f"{size} px",
                                  command=lambda s=size: self.text_widget.configure(font=("Consolas", s)))
        font_menu.config(menu=menu_font)
        ToolTip(font_menu, text_key="main_window.format_toolbar.font_size_tooltip")

        # Color picker
        def choose_color():
            color = colorchooser.askcolor(title=_("dialogs.common.choose_color"))[1]
            if color:
                apply_tag(self.text_widget, color)
                self.text_widget.tag_configure(color, foreground=color)
        btn_color = ttk.Button(row1, text=_("main_window.format_toolbar.color"), width=3, style="Cyan.TButton", command=choose_color)
        btn_color.pack(side=tk.LEFT, padx=1)
        btn_color.i18n_key = "main_window.format_toolbar.color"
        ToolTip(btn_color, text_key="main_window.format_toolbar.color_tooltip")

        # Spacer
        ttk.Label(row1, text="  ").pack(side=tk.LEFT)

        # Heading style
        btn_heading = ttk.Button(row1, text=_("main_window.format_toolbar.heading"), width=3, style="Cyan.TButton",
                                 command=lambda: apply_tag(self.text_widget, "heading"))
        btn_heading.pack(side=tk.LEFT, padx=1)
        btn_heading.i18n_key = "main_window.format_toolbar.heading"
        ToolTip(btn_heading, text_key="main_window.format_toolbar.heading_tooltip")

        # Insert date/time
        btn_datetime = ttk.Button(row1, text=_("main_window.format_toolbar.datetime"), width=3, style="Cyan.TButton",
                                  command=lambda: insert_datetime(self.text_widget))
        btn_datetime.pack(side=tk.LEFT, padx=1)
        btn_datetime.i18n_key = "main_window.format_toolbar.datetime"
        ToolTip(btn_datetime, text_key="main_window.format_toolbar.datetime_tooltip")

        # ========== ROW 2 ==========
        # Align left
        btn_left = ttk.Button(row2, text=_("main_window.format_toolbar.align_left"), width=3, style="Cyan.TButton",
                              command=lambda: align_text(self.text_widget, "left"))
        btn_left.pack(side=tk.LEFT, padx=1)
        btn_left.i18n_key = "main_window.format_toolbar.align_left"
        ToolTip(btn_left, text_key="main_window.format_toolbar.align_left_tooltip")

        # Align center
        btn_center = ttk.Button(row2, text=_("main_window.format_toolbar.align_center"), width=3, style="Cyan.TButton",
                                command=lambda: align_text(self.text_widget, "center"))
        btn_center.pack(side=tk.LEFT, padx=1)
        btn_center.i18n_key = "main_window.format_toolbar.align_center"
        ToolTip(btn_center, text_key="main_window.format_toolbar.align_center_tooltip")

        # Align right
        btn_right = ttk.Button(row2, text=_("main_window.format_toolbar.align_right"), width=3, style="Cyan.TButton",
                               command=lambda: align_text(self.text_widget, "right"))
        btn_right.pack(side=tk.LEFT, padx=1)
        btn_right.i18n_key = "main_window.format_toolbar.align_right"
        ToolTip(btn_right, text_key="main_window.format_toolbar.align_right_tooltip")

        # Justify
        btn_justify = ttk.Button(row2, text=_("main_window.format_toolbar.align_justify"), width=3, style="Cyan.TButton",
                                 command=lambda: align_text(self.text_widget, "justify"))
        btn_justify.pack(side=tk.LEFT, padx=1)
        btn_justify.i18n_key = "main_window.format_toolbar.align_justify"
        ToolTip(btn_justify, text_key="main_window.format_toolbar.align_justify_tooltip")

        # Spacer
        ttk.Label(row2, text="  ").pack(side=tk.LEFT)

        # Increase indent
        btn_indent = ttk.Button(row2, text=_("main_window.format_toolbar.indent_increase"), width=3, style="Cyan.TButton",
                                command=lambda: increase_indent(self.text_widget))
        btn_indent.pack(side=tk.LEFT, padx=1)
        btn_indent.i18n_key = "main_window.format_toolbar.indent_increase"
        ToolTip(btn_indent, text_key="main_window.format_toolbar.indent_increase_tooltip")

        # Decrease indent
        btn_dedent = ttk.Button(row2, text=_("main_window.format_toolbar.indent_decrease"), width=3, style="Cyan.TButton",
                                command=lambda: decrease_indent(self.text_widget))
        btn_dedent.pack(side=tk.LEFT, padx=1)
        btn_dedent.i18n_key = "main_window.format_toolbar.indent_decrease"
        ToolTip(btn_dedent, text_key="main_window.format_toolbar.indent_decrease_tooltip")

        # Spacer
        ttk.Label(row2, text="  ").pack(side=tk.LEFT)

        # Numbered list
        btn_numbered = ttk.Button(row2, text=_("main_window.format_toolbar.numbered_list"), width=3, style="Cyan.TButton",
                                  command=lambda: insert_numbered_list(self.text_widget, self.app))
        btn_numbered.pack(side=tk.LEFT, padx=1)
        btn_numbered.i18n_key = "main_window.format_toolbar.numbered_list"
        ToolTip(btn_numbered, text_key="main_window.format_toolbar.numbered_list_tooltip")

        # Bullet list
        btn_bullet = ttk.Button(row2, text=_("main_window.format_toolbar.bullet_list"), width=3, style="Cyan.TButton",
                                command=lambda: insert_bullet(self.text_widget))
        btn_bullet.pack(side=tk.LEFT, padx=1)
        btn_bullet.i18n_key = "main_window.format_toolbar.bullet_list"
        ToolTip(btn_bullet, text_key="main_window.format_toolbar.bullet_list_tooltip")

        # Spacer
        ttk.Label(row2, text="  ").pack(side=tk.LEFT)

        # Insert table
        btn_table = ttk.Button(row2, text=_("main_window.format_toolbar.table"), width=3, style="Cyan.TButton",
                               command=lambda: insert_table(self.text_widget))
        btn_table.pack(side=tk.LEFT, padx=1)
        btn_table.i18n_key = "main_window.format_toolbar.table"
        ToolTip(btn_table, text_key="main_window.format_toolbar.table_tooltip")

        # Spacer
        ttk.Label(row2, text="  ").pack(side=tk.LEFT)

        # Export HTML
        btn_export_html = ttk.Button(row2, text=_("main_window.format_toolbar.export_html"), width=5, style="Cyan.TButton",
                                     command=lambda: export_html(self.text_widget))
        btn_export_html.pack(side=tk.LEFT, padx=1)
        btn_export_html.i18n_key = "main_window.format_toolbar.export_html"
        ToolTip(btn_export_html, text_key="main_window.format_toolbar.export_html_tooltip")

        # Import HTML
        btn_import_html = ttk.Button(row2, text=_("main_window.format_toolbar.import_html"), width=6, style="Cyan.TButton",
                                     command=lambda: import_html(self.text_widget))
        btn_import_html.pack(side=tk.LEFT, padx=1)
        btn_import_html.i18n_key = "main_window.format_toolbar.import_html"
        ToolTip(btn_import_html, text_key="main_window.format_toolbar.import_html_tooltip")