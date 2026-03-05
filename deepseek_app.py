#!/usr/bin/env python3
# deepseek_app.py - Aplicativo independente para consulta DeepSeek

import tkinter as tk
import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from frontend.deepseek_window import DeepSeekWindow

if __name__ == "__main__":
    # Oculta o console (se estiver em modo gráfico)
    try:
        root = tk.Tk()
        root.withdraw()  # esconde a janela raiz
        # Cria a janela DeepSeek sem passar main_app
        win = DeepSeekWindow(root, None)
        root.mainloop()
    except Exception as e:
        print(f"Erro ao iniciar DeepSeek: {e}")
        sys.exit(1)