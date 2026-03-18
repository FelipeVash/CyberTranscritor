#!/usr/bin/env python3
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import subprocess
import sys
from pathlib import Path
from core.frontend.styles import configure_styles

BASE_DIR = Path(__file__).parent

def launch_app(script_name, venv_name):
    if sys.platform == "win32":
        python_exe = BASE_DIR / venv_name / "Scripts" / "python.exe"
    else:
        python_exe = BASE_DIR / venv_name / "bin" / "python"
    script_path = BASE_DIR / script_name
    if not python_exe.exists():
        print(f"Ambiente virtual {venv_name} não encontrado.")
        return
    subprocess.Popen([str(python_exe), str(script_path)])

root = tb.Window(themename="darkly")
root.title("Suíte Transcritor")
root.geometry("400x300")
root.resizable(False, False)

style = tb.Style.get_instance()
configure_styles(style)

frame = tb.Frame(root, padding=20)
frame.pack(fill=BOTH, expand=True)

tb.Label(frame, text="Escolha um aplicativo:", font=("Arial", 14)).pack(pady=10)

tb.Button(frame, text="🎤 Transcritor / Tradutor",
          command=lambda: launch_app("transcritor_app.py", "venv_transcritor"),
          width=30, style="Cyan.TButton").pack(pady=5)

tb.Button(frame, text="🎙️ Meeting Recorder",
          command=lambda: launch_app("meeting_app.py", "venv_meeting"),
          width=30, style="Pink.TButton").pack(pady=5)

tb.Button(frame, text="🤖 DeepSeek Chat",
          command=lambda: launch_app("deepseek_app.py", "venv_deepseek"),
          width=30, style="secondary.TButton").pack(pady=5)

root.mainloop()
