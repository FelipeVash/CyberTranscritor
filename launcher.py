#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
from pathlib import Path

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

root = tk.Tk()
root.title("Suíte Transcritor")
root.geometry("400x300")
root.resizable(False, False)

frame = ttk.Frame(root, padding=20)
frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(frame, text="Escolha um aplicativo:", font=("Arial", 14)).pack(pady=10)

ttk.Button(frame, text="🎤 Transcritor / Tradutor",
           command=lambda: launch_app("main_app.py", "venv_transcritor"),
           width=30).pack(pady=5)

ttk.Button(frame, text="🎙️ Meeting Recorder",
           command=lambda: launch_app("meeting_app.py", "venv_meeting"),
           width=30).pack(pady=5)

ttk.Button(frame, text="🤖 DeepSeek Chat (em breve)",
           state="disabled", width=30).pack(pady=5)

root.mainloop()
