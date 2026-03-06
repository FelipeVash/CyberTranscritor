# backend/dbus/dbus_service.py
"""
D-Bus service for the Cyberpunk Transcriber.
Exposes methods that can be called by global shortcuts or other applications.
Received commands are placed in a queue for safe processing by the controller.
"""

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
from utils.logger import logger

class DBusService(dbus.service.Object):
    """
    D-Bus service object that handles incoming method calls.
    Each method puts a command into the controller's queue.
    """

    def __init__(self, controller, bus_name='studio.transcritor', object_path='/studio/transcritor'):
        """
        Initialize the D-Bus service and register the object.

        Args:
            controller: Reference to the AppController (must have a dbus_queue attribute)
            bus_name: D-Bus bus name
            object_path: D-Bus object path
        """
        self.controller = controller
        self.bus_name_str = bus_name
        self.object_path = object_path

        # Set up the GLib main loop for D-Bus (if not already configured)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        # Get the session bus
        self.bus = dbus.SessionBus()

        # Request the bus name
        self.bus_name = dbus.service.BusName(bus_name, bus=self.bus)

        # Initialize the superclass (dbus.service.Object) with the object path
        dbus.service.Object.__init__(self, self.bus_name, object_path)

        logger.info(f"D-Bus service '{bus_name}' registered at {object_path}")

    # ==================== EXPOSED D-BUS METHODS ====================

    @dbus.service.method('studio.transcritor')
    def toggle_recording(self):
        """Start/stop recording (toggle)."""
        logger.debug("D-BUS: toggle_recording called")
        self.controller.dbus_queue.put(('toggle_recording',))

    @dbus.service.method('studio.transcritor')
    def translate(self):
        """Translate the current transcription."""
        logger.debug("D-BUS: translate called")
        self.controller.dbus_queue.put(('translate',))

    @dbus.service.method('studio.transcritor')
    def save(self):
        """Save the current transcription."""
        logger.debug("D-BUS: save called")
        self.controller.dbus_queue.put(('save',))

    @dbus.service.method('studio.transcritor')
    def correct(self):
        """Correct the current transcription."""
        logger.debug("D-BUS: correct called")
        self.controller.dbus_queue.put(('correct',))

    @dbus.service.method('studio.transcritor')
    def open_deepseek(self):
        """Open the DeepSeek window."""
        logger.debug("D-BUS: open_deepseek called")
        self.controller.dbus_queue.put(('open_deepseek',))

    @dbus.service.method('studio.transcritor')
    def stop_audio(self):
        """Stop any ongoing audio playback."""
        logger.debug("D-BUS: stop_audio called")
        self.controller.dbus_queue.put(('stop_audio',))

    @dbus.service.method('studio.transcritor')
    def toggle_background(self):
        """Toggle background recording mode."""
        logger.debug("D-BUS: toggle_background called")
        self.controller.dbus_queue.put(('toggle_background',))