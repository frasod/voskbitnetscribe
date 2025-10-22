"""
Braun-inspired minimalist styling.
Separated from logic for clarity and maintainability.
"""

from ..core.config import UIConfig


def get_stylesheet(config: UIConfig) -> str:
    """
    Generate application stylesheet.
    Braun aesthetic: clean, purposeful, elegant.
    """
    return f"""
    /* Global application styling */
    QMainWindow, QWidget {{
        background-color: {config.background};
        color: {config.primary};
        font-size: {config.font_size}pt;
        font-family: "Helvetica Neue", "Arial", sans-serif;
    }}
    
    /* Primary buttons - strong presence */
    QPushButton {{
        background-color: {config.primary};
        color: {config.surface};
        border: none;
        padding: 10px 20px;
        font-weight: 500;
        font-size: {config.font_size}pt;
        min-height: 36px;
    }}
    
    QPushButton:hover {{
        background-color: {config.secondary};
    }}
    
    QPushButton:disabled {{
        background-color: {config.accent};
        color: {config.secondary};
    }}
    
    /* Danger button - recording stop */
    QPushButton[danger="true"] {{
        background-color: {config.error};
        color: {config.surface};
    }}
    
    QPushButton[danger="true"]:hover {{
        background-color: #A01828;
    }}
    
    /* Text input areas - clean surfaces */
    QTextEdit, QLineEdit {{
        background-color: {config.surface};
        border: 1px solid {config.accent};
        padding: 8px;
        font-size: {config.font_size}pt;
        color: {config.primary};
    }}
    
    QTextEdit:focus, QLineEdit:focus {{
        border: 1px solid {config.primary};
    }}
    
    QTextEdit:read-only {{
        background-color: {config.background};
    }}
    
    /* Labels - hierarchy through weight */
    QLabel {{
        color: {config.primary};
        font-size: {config.font_size}pt;
        padding: 4px 0px;
    }}
    
    QLabel[heading="true"] {{
        font-weight: 600;
        font-size: {config.font_size + 2}pt;
        padding: 12px 0px;
    }}
    
    QLabel[status="true"] {{
        color: {config.secondary};
        font-size: {config.font_size - 1}pt;
    }}
    
    /* Spacing and layout */
    QVBoxLayout {{
        spacing: 8px;
    }}
    
    QHBoxLayout {{
        spacing: 8px;
    }}
    """


def get_recording_button_style(is_recording: bool, config: UIConfig) -> str:
    """Get dynamic style for recording button."""
    if is_recording:
        return f"""
            QPushButton {{
                background-color: {config.error};
                color: {config.surface};
                border: none;
                padding: 10px 20px;
                font-weight: 500;
                font-size: {config.font_size}pt;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #A01828;
            }}
        """
    else:
        return f"""
            QPushButton {{
                background-color: {config.primary};
                color: {config.surface};
                border: none;
                padding: 10px 20px;
                font-weight: 500;
                font-size: {config.font_size}pt;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: {config.secondary};
            }}
        """
