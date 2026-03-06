# utils/tooltip.py
"""
Tooltip module for displaying help text on hover.
Supports internationalization via text keys.
All logging is done through the centralized logger.
"""

import tkinter as tk
from utils.i18n import _
from utils.logger import logger

class ToolTip:
    """
    Create a tooltip for a given widget.
    The tooltip text can be a fixed string or a translation key.
    """

    # List of all tooltip instances (for potential bulk updates)
    _instances = []

    def __init__(self, widget, text_key=None, text=None):
        """
        Initialize the tooltip.

        Args:
            widget: The widget to attach the tooltip to
            text_key: Internationalization key for the tooltip text
            text: Fixed text (used if text_key is None)
        """
        self.widget = widget
        self.text_key = text_key
        self.text = text
        self.tip_window = None
        ToolTip._instances.append(self)
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)
        widget.bind('<ButtonPress>', self.hide_tip)
        logger.debug(f"ToolTip created for {widget}")

    def update_text(self, new_text_key=None, new_text=None):
        """Update the tooltip text (by key or fixed string)."""
        if new_text_key is not None:
            self.text_key = new_text_key
            self.text = None
            logger.debug(f"ToolTip updated with key: {new_text_key}")
        elif new_text is not None:
            self.text = new_text
            self.text_key = None
            logger.debug("ToolTip updated with fixed text")

    def get_text(self):
        """Return the current text (translated if a key is set)."""
        if self.text_key:
            return _(self.text_key)
        return self.text

    def show_tip(self, event=None):
        """Display the tooltip window near the widget."""
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
        logger.debug(f"ToolTip shown: {self.get_text()}")

    def hide_tip(self, event=None):
        """Destroy the tooltip window."""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
            logger.debug("ToolTip hidden")