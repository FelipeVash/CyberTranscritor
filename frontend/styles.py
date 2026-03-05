# frontend/styles.py
from ttkbootstrap import Style

def configure_styles(style):
    """Configura estilos customizados."""
    style.configure("Cyan.TButton", background="#00ffbf", foreground="black", relief="raised", borderwidth=2)
    style.map("Cyan.TButton",
              background=[("active", "#00cc99"), ("pressed", "#009966")],
              foreground=[("active", "black")])
    style.configure("Pink.TButton", background="#ff0080", foreground="white", relief="raised", borderwidth=2)
    style.map("Pink.TButton",
              background=[("active", "#cc0066"), ("pressed", "#99004d")],
              foreground=[("active", "white")])
    style.configure("Magenta.TButton", background="#ff00ff", foreground="black", relief="raised", borderwidth=2)
    style.map("Magenta.TButton",
              background=[("active", "#cc00cc"), ("pressed", "#990099")],
              foreground=[("active", "black")])

    # Bordas dos Labelframe
    style.configure("TLabelframe", bordercolor="#00ffbf", lightcolor="#00ffbf", darkcolor="#00ffbf",
                    relief="solid", borderwidth=2)
    style.configure("TLabelframe.Label", foreground="#00ffbf")