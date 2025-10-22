"""
Application entry point.
Lean orchestration - configuration and initialization only.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.core.config import Config
from src.ui import MainWindow


def main() -> int:
    """
    Application entry point.
    Returns exit code.
    """
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("VOSK BitNet Scribe")
    app.setOrganizationName("VoskBitnetScribe")
    
    # Load configuration
    config = Config.from_environment()
    
    # Validate configuration
    is_valid, errors = config.validate()
    if not is_valid:
        error_msg = "Configuration errors:\n\n" + "\n".join(f"• {e}" for e in errors)
        QMessageBox.critical(None, "Configuration Error", error_msg)
        return 1
    
    # Create and show main window
    window = MainWindow(config)
    window.show()
    
    # Run application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
