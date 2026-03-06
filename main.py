# main.py
from controller.app_controller import AppController
from frontend.main_window import TranscriptionStudio

def main():
    controller = AppController()
    app = TranscriptionStudio(controller)
    app.root.mainloop()

if __name__ == "__main__":
    main()