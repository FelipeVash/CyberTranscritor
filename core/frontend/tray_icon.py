# frontend/tray_icon.py
"""
System tray icon management.
Provides a menu to show/hide the main window and quit the application.
All logging is done through the centralized logger.
"""

import threading
import pystray
from PIL import Image, ImageDraw
import subprocess
import os
from core.utils.i18n import _
from core.utils.logger import logger

class TrayIcon:
    """System tray icon with menu for window control."""

    def __init__(self, app):
        """
        Initialize the tray icon.

        Args:
            app: Reference to the main window (TranscriptionStudio instance)
        """
        self.app = app
        self.icon = None
        self.thread = None
        logger.debug("TrayIcon initialized")

    def create_image(self):
        """Create a simple icon image (a colored circle)."""
        image = Image.new('RGB', (64, 64), color='#00ffbf')
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill='#ff0080', outline='#ff00ff', width=3)
        return image

    def on_show(self, icon, item):
        """Menu callback to show the main window."""
        logger.debug("Tray menu: Show clicked")
        self.app.show_window()

    def on_hide(self, icon, item):
        """Menu callback to hide the main window."""
        logger.debug("Tray menu: Hide clicked")
        self.app.hide_window()

    def on_quit(self, icon, item):
        """Menu callback to quit the application."""
        logger.info("Tray menu: Quit clicked")
        # Stop any audio before quitting
        if hasattr(self.app, 'stop_all_audio'):
            self.app.stop_all_audio()
        self.app.quit_app()

    def setup_menu(self):
        """Build the tray menu using translated strings."""
        return (
            pystray.MenuItem(_("tray.menu.show"), self.on_show),
            pystray.MenuItem(_("tray.menu.hide"), self.on_hide),
            pystray.MenuItem(_("tray.menu.quit"), self.on_quit),
        )

    def run(self):
        """Run the tray icon (blocking)."""
        image = self.create_image()
        menu = self.setup_menu()
        self.icon = pystray.Icon("transcritor", image, _("main_window.title"), menu)
        logger.info("Tray icon started")
        self.icon.run()

    def start(self):
        """Start the tray icon in a background thread."""
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        logger.debug("Tray icon thread started")

    def stop(self):
        """Stop the tray icon."""
        if self.icon:
            self.icon.stop()
            logger.debug("Tray icon stopped")