#!/usr/bin/env python3
# main.py
# Ponto de entrada da aplicação

from frontend.main_window import TranscriptionStudio

if __name__ == "__main__":
    app = TranscriptionStudio()
    app.root.mainloop()