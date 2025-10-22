"""
System clipboard integration service.
Simple, focused responsibility.
"""

from typing import Optional
from PyQt6.QtWidgets import QApplication


class ClipboardService:
    """
    Manages system clipboard operations.
    Platform-agnostic through Qt abstraction.
    """
    
    @staticmethod
    def copy_text(text: str) -> tuple[bool, Optional[str]]:
        """
        Copy text to system clipboard.
        Returns (success, error_message).
        """
        try:
            clipboard = QApplication.clipboard()
            if not clipboard:
                return False, "Clipboard not available"
            
            clipboard.setText(text)
            return True, None
            
        except Exception as e:
            return False, f"Failed to copy to clipboard: {e}"
    
    @staticmethod
    def get_text() -> Optional[str]:
        """Get text from clipboard if available."""
        try:
            clipboard = QApplication.clipboard()
            if not clipboard:
                return None
            return clipboard.text()
        except Exception:
            return None
