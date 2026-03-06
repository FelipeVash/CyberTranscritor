# frontend/tray_icon.py
import threading
import pystray
from PIL import Image, ImageDraw
import subprocess
import os
from utils.i18n import _

class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self.thread = None

    def create_image(self):
        image = Image.new('RGB', (64, 64), color='#00ffbf')
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill='#ff0080', outline='#ff00ff', width=3)
        return image

    def on_show(self, icon, item):
        self.app.show_window()

    def on_hide(self, icon, item):
        self.app.hide_window()

    def on_quit(self, icon, item):
        if hasattr(self.app, 'stop_all_audio'):
            self.app.stop_all_audio()
        self.app.quit_app()

    def setup_menu(self):
        return (
            pystray.MenuItem(_("tray.menu.show"), self.on_show),
            pystray.MenuItem(_("tray.menu.hide"), self.on_hide),
            pystray.MenuItem(_("tray.menu.quit"), self.on_quit),
        )

    def run(self):
        image = self.create_image()
        menu = self.setup_menu()
        self.icon = pystray.Icon("transcritor", image, "Studio de Transcrição", menu)
        self.icon.run()

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        if self.icon:
            self.icon.stop()