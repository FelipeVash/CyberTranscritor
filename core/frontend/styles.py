# frontend/styles.py
"""
Custom ttk styles for the Cyberpunk theme.
Defines button styles with different font weights and decorations.
All buttons use Arial 12 bold for consistent height.
"""

from ttkbootstrap import Style

def configure_styles(style):
    """
    Configure custom ttk styles.

    Args:
        style: ttkbootstrap Style object
    """
    # Base button padding to ensure uniform height
    button_padding = (10, 5)  # Increased vertical padding to 4
    base_font = ("Arial", 12, "bold")
    bold_italic_font = ("Arial", 12, "bold italic")

    # Base Cyan button style (normal)
    style.configure("Cyan.TButton",
                    background="#00ffbf",
                    foreground="black",
                    relief="raised",
                    borderwidth=2,
                    font=base_font,
                    padding=button_padding)
    style.map("Cyan.TButton",
              background=[("active", "#00cc99"), ("pressed", "#009966")],
              foreground=[("active", "black")])

    # Bold button style (already bold, same as Cyan)
    style.configure("Bold.TButton",
                    background="#00ffbf",
                    foreground="black",
                    relief="raised",
                    borderwidth=2,
                    font=base_font,
                    padding=button_padding)
    style.map("Bold.TButton",
              background=[("active", "#00cc99"), ("pressed", "#009966")],
              foreground=[("active", "black")])

    # Italic button style (bold italic)
    style.configure("Italic.TButton",
                    background="#00ffbf",
                    foreground="black",
                    relief="raised",
                    borderwidth=2,
                    font=bold_italic_font,
                    padding=button_padding)
    style.map("Italic.TButton",
              background=[("active", "#00cc99"), ("pressed", "#009966")],
              foreground=[("active", "black")])

    # Underline button style (no underline in Tkinter buttons, use normal)
    style.configure("Underline.TButton",
                    background="#00ffbf",
                    foreground="black",
                    relief="raised",
                    borderwidth=2,
                    font=base_font,
                    padding=button_padding)
    style.map("Underline.TButton",
              background=[("active", "#00cc99"), ("pressed", "#009966")],
              foreground=[("active", "black")])

    # Strike button style (no overstrike in buttons)
    style.configure("Strike.TButton",
                    background="#00ffbf",
                    foreground="black",
                    relief="raised",
                    borderwidth=2,
                    font=base_font,
                    padding=button_padding)
    style.map("Strike.TButton",
              background=[("active", "#00cc99"), ("pressed", "#009966")],
              foreground=[("active", "black")])

    # Pink button style
    style.configure("Pink.TButton",
                    background="#ff0080",
                    foreground="white",
                    relief="raised",
                    borderwidth=2,
                    font=base_font,
                    padding=button_padding)
    style.map("Pink.TButton",
              background=[("active", "#cc0066"), ("pressed", "#99004d")],
              foreground=[("active", "white")])

    # Magenta button style
    style.configure("Magenta.TButton",
                    background="#ff00ff",
                    foreground="black",
                    relief="raised",
                    borderwidth=2,
                    font=base_font,
                    padding=button_padding)
    style.map("Magenta.TButton",
              background=[("active", "#cc00cc"), ("pressed", "#990099")],
              foreground=[("active", "black")])

    # Secondary button style (used for "Clear", etc.)
    style.configure("secondary.TButton",
                    font=base_font,
                    padding=button_padding)

    # LabelFrame borders
    style.configure("TLabelframe",
                    bordercolor="#00ffbf",
                    lightcolor="#00ffbf",
                    darkcolor="#00ffbf",
                    relief="solid",
                    borderwidth=2)
    style.configure("TLabelframe.Label",
                    foreground="#00ffbf")