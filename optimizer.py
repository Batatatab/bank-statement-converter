"""optimizer.py

Performance, memory, and Windows subsystem optimization helpers.
"""

import ctypes
import gc
import os
import sys


def setup_windows_environment(app_id: str = "custom.bankconverter.app.1"):
    """Configures high-DPI awareness and registers a dedicated AppUserModelID

    so Windows displays the custom icon properly on the title bar and taskbar.
    """
    if sys.platform != "win32":
        return

    try:
        # 1. Register unique process ID with Windows Shell
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    try:
        # 2. Enable Per-Monitor DPI awareness (prevents blurry Tahoma fonts)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_asset_path(filename: str) -> str:
    """Resolves the absolute path of an asset (icon, config, etc.)

    works both in local development and inside a PyInstaller .exe bundle.
    """
    if hasattr(sys, "_MEIPASS"):
        # Running inside PyInstaller unpacked directory
        base_dir = sys._MEIPASS
    else:
        # Running in standard Python development
        base_dir = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_dir, filename)


def dispatch_to_main_thread(root, func, *args, **kwargs):
    """Schedules a function to run safely on the Tkinter main event loop."""
    root.after(0, lambda: func(*args, **kwargs))


class StatementMemoryManager:
    """Manages heap cleanup during long statement extractions."""

    def __init__(self, gc_interval: int = 15):
        self.gc_interval = gc_interval

    def on_page_processed(self, current_page_index: int):
        """Flushes unreferenced pdfminer layout trees every N pages."""
        if current_page_index > 0 and current_page_index % self.gc_interval == 0:
            gc.collect()

    def finalize(self):
        """Full garbage collection cycle after export completion."""
        gc.collect()